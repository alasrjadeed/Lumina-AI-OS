from __future__ import annotations

import json
import os
import re
import time
import uuid
from typing import Any

import httpx

_WORKFLOWS_DIR = os.path.expanduser("~/.lumina/workflows")

WORKFLOW_CATEGORIES = ["automation","data","communication","development",
    "crm","ecommerce","ai","devops","marketing","finance","custom"]

NODE_CATEGORIES = ["triggers","ai","flow-control","data-transform","file-media",
    "communication","crm-sales","project-management","ecommerce",
    "cloud-infra","database","social","developer-tools","http-rest","utilities","experimental"]

NODE_REGISTRY: dict[str, dict] = {}
NODE_TYPE_MAP: dict[str, str] = {}
REVERSE_NODE_MAP: dict[str, str] = {}

def _reg(node_type,display_name,category,color,icon,n8n_type=None,
           default_label=None,description="",trigger=False,
           config_schema=None,defaults=None,hide=False):
    entry = {"type":node_type,"displayName":display_name,
        "category":category,"color":color,"icon":icon,
        "defaultLabel":default_label or display_name,
        "description":description,"trigger":trigger,"hide":hide,
        "configSchema":config_schema or [],
        "defaults":defaults or {}}
    NODE_REGISTRY[node_type] = entry
    nt = n8n_type or f"n8n-nodes-base.{node_type}"
    NODE_TYPE_MAP[node_type] = nt
    REVERSE_NODE_MAP[nt] = node_type
    return entry


def F_string(n,**kw): return {"name":n,"type":"string",**kw}
def F_number(n,**kw): return {"name":n,"type":"number",**kw}
def F_boolean(n,**kw): return {"name":n,"type":"boolean",**kw}
def F_select(n,opts,**kw): return {"name":n,"type":"select","options":opts,**kw}
def F_code(n,**kw): return {"name":n,"type":"code",**kw}
def F_json(n,**kw): return {"name":n,"type":"json",**kw}
def F_credentials(n,**kw): return {"name":n,"type":"credentials",**kw}
def F_expression(n,**kw): return {"name":n,"type":"expression",**kw}
def F_notice(n,**kw): return {"name":n,"type":"notice","readOnly":True,**kw}


_reg('webhook','Webhook','triggers','#ff6b6b','Zap',n8n_type='n8n-nodes-base.webhook',description='Receive webhook requests',trigger=True,config_schema=[F_select("method",[{"label":"GET","value":"GET"},{"label":"POST","value":"POST"},{"label":"PUT","value":"PUT"},{"label":"PATCH","value":"PATCH"},{"label":"DELETE","value":"DELETE"}],label="Method",default="POST"),F_string("path",label="Path",default="/webhook")],defaults={"method":"POST","path":"/webhook"})
_reg('schedule','Schedule','triggers','#ffa502','Clock',n8n_type='n8n-nodes-base.scheduleTrigger',description='Trigger on cron schedule',trigger=True,config_schema=[F_select("cron",[{"label":"Every Hour","value":"0 * * * *"},{"label":"Daily 8am","value":"0 8 * * *"},{"label":"Custom","value":"custom"}],label="Schedule",default="0 * * * *"),F_string("cronExpr",label="Cron",default="0 * * * *")],defaults={"cron":"0 * * * *","cronExpr":"0 * * * *"})
_reg('manual','Manual Trigger','triggers','#ffa502','Play',n8n_type='n8n-nodes-base.manualTrigger',description='Start workflow manually',trigger=True,config_schema=[],defaults={})
_reg('form','Form Trigger','triggers','#ff6b6b','FormInput',n8n_type='n8n-nodes-base.form',description='Trigger via web form',trigger=True,config_schema=[F_string("title",label="Title",default="Contact Form"),F_code("fields",label="Fields JSON",default="[]")],defaults={"title":"Web Form","fields":"[]"})
_reg('webhookListener','Webhook Response','triggers','#ff6b6b','Reply',n8n_type='n8n-nodes-base.respondToWebhook',description='Send webhook response',trigger=False,config_schema=[F_select("respondWith",[{"label":"JSON","value":"json"},{"label":"Text","value":"text"}],label="Type",default="json"),F_code("body",label="Body",default="{}")],defaults={"respondWith":"json","body":"{}"})
_reg('llm','LLM (Chat)','ai','#a855f7','Brain',n8n_type='n8n-nodes-base.lmChatOpenAi',description='Call an LLM',trigger=False,config_schema=[F_select("provider",[{"label":"OpenAI","value":"openai"},{"label":"Anthropic","value":"anthropic"},{"label":"Gemini","value":"gemini"},{"label":"Ollama","value":"ollama"},{"label":"Groq","value":"groq"},{"label":"DeepSeek","value":"deepseek"}],label="Provider",default="openai"),F_string("model",label="Model",default="gpt-4o"),F_code("messages",label="Messages",default="[]"),F_number("temperature",label="Temperature",default=0.7),F_number("maxTokens",label="Max Tokens",default=2048)],defaults={"provider":"openai","model":"gpt-4o","messages":"[]","temperature":0.7,"maxTokens":2048})
_reg('agent','AI Agent','ai','#7c3aed','Bot',n8n_type='n8n-nodes-base.agent',description='AI agent with tools',trigger=False,config_schema=[F_select("type",[{"label":"ReAct","value":"react"},{"label":"Conversational","value":"conversational"},{"label":"OpenAI Functions","value":"openai_functions"}],label="Agent Type",default="react"),F_code("systemPrompt",label="System Prompt",default="You are a helpful assistant."),F_string("model",label="Model",default="gpt-4o"),F_number("maxIterations",label="Max Iterations",default=10)],defaults={"type":"react","systemPrompt":"You are a helpful assistant.","model":"gpt-4o","maxIterations":10})
_reg('vectorStore','Vector Store','ai','#a855f7','Database',n8n_type='n8n-nodes-base.vectorStorePinecone',description='Vector DB for RAG',trigger=False,config_schema=[F_select("storeType",[{"label":"In-Memory","value":"memory"},{"label":"Pinecone","value":"pinecone"},{"label":"Qdrant","value":"qdrant"},{"label":"ChromaDB","value":"chromadb"}],label="Store",default="memory"),F_select("operation",[{"label":"Insert","value":"insert"},{"label":"Retrieve","value":"retrieve"},{"label":"Delete","value":"delete"}],label="Operation",default="retrieve"),F_string("indexName",label="Index",default="documents"),F_number("topK",label="Top K",default=4)],defaults={"storeType":"memory","operation":"retrieve","indexName":"documents","topK":4})
_reg('embeddings','Embeddings','ai','#a855f7','Hash',n8n_type='n8n-nodes-base.embeddingsOpenAi',description='Generate embeddings',trigger=False,config_schema=[F_select("provider",[{"label":"OpenAI","value":"openai"},{"label":"Cohere","value":"cohere"},{"label":"Gemini","value":"gemini"}],label="Provider",default="openai"),F_string("model",label="Model",default="text-embedding-3-small")],defaults={"provider":"openai","model":"text-embedding-3-small"})
_reg('tool','Tool','ai','#a855f7','Wrench',n8n_type='n8n-nodes-base.tool',description='Tool for AI agents',trigger=False,config_schema=[F_select("toolType",[{"label":"HTTP Request","value":"http"},{"label":"Code","value":"code"},{"label":"Web Search","value":"webSearch"},{"label":"Vector Store","value":"vectorStore"}],label="Tool Type",default="http"),F_string("name",label="Name",default="my_tool"),F_string("description",label="Description",default="")],defaults={"toolType":"http","name":"my_tool","description":""})
_reg('memory','Memory','ai','#a855f7','MessageCircle',n8n_type='n8n-nodes-base.memory',description='Conversation memory',trigger=False,config_schema=[F_select("type",[{"label":"Window Buffer","value":"window"},{"label":"Summary","value":"summary"}],label="Type",default="window"),F_number("windowSize",label="Window Size",default=10)],defaults={"type":"window","windowSize":10})
_reg('textSplitter','Text Splitter','ai','#a855f7','Scissors',n8n_type='n8n-nodes-base.textSplitter',description='Split text into chunks',trigger=False,config_schema=[F_select("method",[{"label":"Recursive","value":"recursive"},{"label":"Token","value":"token"},{"label":"Markdown","value":"markdown"}],label="Method",default="recursive"),F_number("chunkSize",label="Chunk Size",default=1000),F_number("overlap",label="Overlap",default=200)],defaults={"method":"recursive","chunkSize":1000,"overlap":200})
_reg('documentLoader','Doc Loader','ai','#a855f7','FileText',n8n_type='n8n-nodes-base.documentLoader',description='Load documents',trigger=False,config_schema=[F_select("source",[{"label":"Text","value":"text"},{"label":"File","value":"file"},{"label":"URL","value":"url"}],label="Source",default="text"),F_code("data",label="Content",default="")],defaults={"source":"text","data":""})
_reg('outputParser','Output Parser','ai','#a855f7','AlignCenter',n8n_type='n8n-nodes-base.outputParser',description='Parse LLM output',trigger=False,config_schema=[F_select("format",[{"label":"JSON","value":"json"},{"label":"CSV","value":"csv"},{"label":"Auto-Fix","value":"auto_fix"}],label="Format",default="json")],defaults={"format":"json"})
_reg('aiTransform','AI Transform','ai','#a855f7','Shuffle',n8n_type='n8n-nodes-base.aiTransform',description='AI-powered transform',trigger=False,config_schema=[F_code("instruction",label="Instruction",default="Summarize the input")],defaults={"instruction":"Summarize the input"})
_reg('if','If Condition','flow-control','#0abde3','GitBranch',n8n_type='n8n-nodes-base.if',description='Conditional routing',trigger=False,config_schema=[F_select("comparison",[{"label":"Equal","value":"eq"},{"label":"Not Equal","value":"neq"},{"label":"Greater Than","value":"gt"},{"label":"Less Than","value":"lt"},{"label":"Contains","value":"contains"},{"label":"Starts With","value":"startsWith"},{"label":"Ends With","value":"endsWith"},{"label":"Is Empty","value":"isEmpty"},{"label":"Exists","value":"exists"}],label="Comparison",default="eq"),F_expression("value1",label="Value 1",default=""),F_expression("value2",label="Value 2",default="")],defaults={"comparison":"eq","value1":"","value2":""})
_reg('switch','Switch','flow-control','#0abde3','GitFork',n8n_type='n8n-nodes-base.switch',description='Multi-route switch',trigger=False,config_schema=[F_expression("field",label="Field",default=""),F_code("rules",label="Rules JSON",default="[]")],defaults={"field":"","rules":"[]"})
_reg('merge','Merge','flow-control','#0abde3','Merge',n8n_type='n8n-nodes-base.merge',description='Merge data streams',trigger=False,config_schema=[F_select("mode",[{"label":"Combine","value":"combine"},{"label":"Merge by Key","value":"merge"},{"label":"Append","value":"append"}],label="Mode",default="combine"),F_string("key",label="Merge Key",default="id")],defaults={"mode":"combine","key":"id"})
_reg('splitInBatches','Split In Batches','flow-control','#0abde3','List',n8n_type='n8n-nodes-base.splitInBatches',description='Batch processing',trigger=False,config_schema=[F_number("batchSize",label="Batch Size",default=10)],defaults={"batchSize":10})
_reg('loop','Loop','flow-control','#0abde3','Repeat',n8n_type='n8n-nodes-base.loop',description='Loop over items',trigger=False,config_schema=[F_select("mode",[{"label":"For Each","value":"forEach"},{"label":"Fixed Count","value":"fixed"}],label="Mode",default="forEach"),F_number("count",label="Count",default=5)],defaults={"mode":"forEach","count":5})
_reg('wait','Wait/Delay','flow-control','#0abde3','Clock',n8n_type='n8n-nodes-base.wait',description='Pause execution',trigger=False,config_schema=[F_select("unit",[{"label":"Seconds","value":"seconds"},{"label":"Minutes","value":"minutes"},{"label":"Hours","value":"hours"}],label="Unit",default="seconds"),F_number("amount",label="Amount",default=1)],defaults={"unit":"seconds","amount":1})
_reg('stopAndError','Stop & Error','flow-control','#ff4757','OctagonAlert',n8n_type='n8n-nodes-base.stopAndError',description='Stop with error',trigger=False,config_schema=[F_string("message",label="Error Message",default="Workflow error")],defaults={"message":"Workflow error"})
_reg('noOp','No Operation','flow-control','#0abde3','Minus',n8n_type='n8n-nodes-base.noOp',description='Pass through',trigger=False,config_schema=[],defaults={})
_reg('stickyNote','Sticky Note','flow-control','#0abde3','StickyNote',n8n_type='n8n-nodes-base.stickyNote',description='Add note to canvas',trigger=False,config_schema=[F_code("content",label="Content",default="Note here...")],defaults={"content":"Note here..."})
_reg('executeWorkflow','Execute Workflow','flow-control','#0abde3','GitBranch',n8n_type='n8n-nodes-base.executeWorkflow',description='Run sub-workflow',trigger=False,config_schema=[F_string("workflowId",label="Workflow ID",default=""),F_select("mode",[{"label":"Sync","value":"sync"},{"label":"Async","value":"async"}],label="Mode",default="sync")],defaults={"mode":"sync"})
_reg('set','Set Data','data-transform','#2ed573','Variable',n8n_type='n8n-nodes-base.set',description='Set field values',trigger=False,config_schema=[F_code("values",label="Values JSON",default="{}"),F_select("mode",[{"label":"Set","value":"set"},{"label":"Overwrite","value":"overwrite"},{"label":"Delete","value":"delete"}],label="Mode",default="set")],defaults={"values":"{}","mode":"set"})
_reg('code','Code','data-transform','#2ed573','Terminal',n8n_type='n8n-nodes-base.code',description='Run custom code',trigger=False,config_schema=[F_select("language",[{"label":"JavaScript","value":"javascript"},{"label":"Python","value":"python"}],label="Language",default="javascript"),F_code("source",label="Code",default="// code here")],defaults={"language":"javascript","source":"// code here"})
_reg('function','Function','data-transform','#2ed573','FunctionSquare',n8n_type='n8n-nodes-base.function',description='JS function per item',trigger=False,config_schema=[F_code("code",label="Function Code",default="return item;")],defaults={"code":"return item;"})
_reg('itemLists','Item Lists','data-transform','#2ed573','List',n8n_type='n8n-nodes-base.itemLists',description='Manipulate lists',trigger=False,config_schema=[F_select("operation",[{"label":"Summarize","value":"summarize"},{"label":"Sort","value":"sort"},{"label":"Limit","value":"limit"},{"label":"Remove Duplicates","value":"dedupe"}],label="Operation",default="summarize")],defaults={"operation":"summarize"})
_reg('compareDatasets','Compare Datasets','data-transform','#2ed573','Columns3',n8n_type='n8n-nodes-base.compareDatasets',description='Find differences',trigger=False,config_schema=[F_string("field1",label="Field 1",default="id"),F_string("field2",label="Field 2",default="id")],defaults={"field1":"id","field2":"id"})
_reg('renameKeys','Rename Keys','data-transform','#2ed573','Replace',n8n_type='n8n-nodes-base.renameKeys',description='Rename object keys',trigger=False,config_schema=[F_code("mappings",label="Mappings JSON",default="{}")],defaults={"mappings":"{}"})
_reg('transform','Transform','data-transform','#2ed573','Shuffle',n8n_type='n8n-nodes-base.transform',description='Apply transforms',trigger=False,config_schema=[F_code("rules",label="Rules JSON",default="[]")],defaults={"rules":"[]"})
_reg('files','Files','file-media','#1e90ff','File',n8n_type='n8n-nodes-base.files',description='File operations',trigger=False,config_schema=[F_select("operation",[{"label":"Read","value":"read"},{"label":"Write","value":"write"},{"label":"List","value":"list"}],label="Operation",default="read"),F_string("path",label="Path",default="/tmp/data.txt")],defaults={"operation":"read","path":"/tmp/data.txt"})
_reg('spreadsheetFile','Spreadsheet File','file-media','#1e90ff','FileSpreadsheet',n8n_type='n8n-nodes-base.spreadsheetFile',description='Read/write CSV/Excel',trigger=False,config_schema=[F_select("operation",[{"label":"Read CSV","value":"read"},{"label":"Write CSV","value":"write"}],label="Operation",default="read"),F_string("filePath",label="File Path",default="/tmp/data.csv")],defaults={"operation":"read","filePath":"/tmp/data.csv"})
_reg('readPdf','Read PDF','file-media','#1e90ff','FileText',n8n_type='n8n-nodes-base.readPdf',description='Extract PDF text',trigger=False,config_schema=[F_string("filePath",label="File Path",default="/tmp/doc.pdf")],defaults={"filePath":"/tmp/doc.pdf"})
_reg('compression','Compression','file-media','#1e90ff','Archive',n8n_type='n8n-nodes-base.compression',description='Zip/unzip files',trigger=False,config_schema=[F_select("operation",[{"label":"Compress","value":"compress"},{"label":"Decompress","value":"decompress"}],label="Operation",default="compress"),F_select("format",[{"label":"ZIP","value":"zip"},{"label":"GZip","value":"gzip"}],label="Format",default="zip")],defaults={"operation":"compress","format":"zip"})
_reg('crypto','Crypto','file-media','#1e90ff','Lock',n8n_type='n8n-nodes-base.crypto',description='Encrypt/hash/sign',trigger=False,config_schema=[F_select("operation",[{"label":"Hash","value":"hash"},{"label":"Encrypt","value":"encrypt"},{"label":"Decrypt","value":"decrypt"}],label="Operation",default="hash"),F_select("algorithm",[{"label":"SHA-256","value":"sha256"},{"label":"SHA-512","value":"sha512"},{"label":"AES-256","value":"aes256"}],label="Algorithm",default="sha256")],defaults={"operation":"hash","algorithm":"sha256"})
_reg('markdown','Markdown','file-media','#1e90ff','FileText',n8n_type='n8n-nodes-base.markdown',description='Markdown conversion',trigger=False,config_schema=[F_select("operation",[{"label":"To HTML","value":"toHtml"},{"label":"To Text","value":"toText"}],label="Operation",default="toHtml")],defaults={"operation":"toHtml"})
_reg('htmlExtract','HTML Extract','file-media','#1e90ff','Code',n8n_type='n8n-nodes-base.htmlExtract',description='Extract HTML data',trigger=False,config_schema=[F_string("selector",label="CSS Selector",default=".content"),F_string("attribute",label="Attribute",default="textContent")],defaults={"selector":".content","attribute":"textContent"})
_reg('emailSend','Send Email','communication','#ff4757','Mail',n8n_type='n8n-nodes-base.emailSend',description='Send email via SMTP',trigger=False,config_schema=[F_string("to",label="To",default=""),F_string("subject",label="Subject",default=""),F_code("body",label="Body HTML",default="")],defaults={"to":"","subject":"","body":""})
_reg('slack','Slack','communication','#4a154b','MessageSquare',n8n_type='n8n-nodes-base.slack',description='Slack integration',trigger=False,config_schema=[F_select("operation",[{"label":"Send Message","value":"send"},{"label":"Get Messages","value":"get"}],label="Operation",default="send"),F_string("channel",label="Channel",default="#general"),F_code("text",label="Text",default="Hello!")],defaults={"operation":"send","channel":"#general","text":"Hello!"})
_reg('discord','Discord','communication','#5865f2','MessageCircle',n8n_type='n8n-nodes-base.discord',description='Discord integration',trigger=False,config_schema=[F_string("webhookUrl",label="Webhook URL",default=""),F_code("content",label="Content",default="Hello!")],defaults={"webhookUrl":"","content":"Hello!"})
_reg('telegram','Telegram','communication','#0088cc','Send',n8n_type='n8n-nodes-base.telegram',description='Telegram bot',trigger=False,config_schema=[F_string("chatId",label="Chat ID",default=""),F_code("text",label="Message",default="Hello!")],defaults={"chatId":"","text":"Hello!"})
_reg('twilio','Twilio SMS','communication','#f22f46','Phone',n8n_type='n8n-nodes-base.twilio',description='Send SMS',trigger=False,config_schema=[F_string("to",label="Phone",default=""),F_string("body",label="Message",default="Hello!")],defaults={"to":"","body":"Hello!"})
_reg('whatsApp','WhatsApp','communication','#25d366','MessageCircle',n8n_type='n8n-nodes-base.whatsApp',description='WhatsApp messages',trigger=False,config_schema=[F_string("to",label="Phone",default=""),F_string("body",label="Message",default="Hello!")],defaults={"to":"","body":"Hello!"})
_reg('salesforce','Salesforce','crm-sales','#00a1e0','Cloud',n8n_type='n8n-nodes-base.salesforce',description='Salesforce CRM',trigger=False,config_schema=[F_select("operation",[{"label":"Query","value":"query"},{"label":"Create Record","value":"create"},{"label":"Get Record","value":"get"},{"label":"Update","value":"update"}],label="Operation",default="query"),F_string("object",label="Object Type",default="Contact")],defaults={"operation":"query","object":"Contact"})
_reg('hubspot','HubSpot','crm-sales','#ff7a59','Cloud',n8n_type='n8n-nodes-base.hubspot',description='HubSpot CRM',trigger=False,config_schema=[F_select("operation",[{"label":"Create Contact","value":"createContact"},{"label":"Get Contact","value":"getContact"},{"label":"Create Deal","value":"createDeal"}],label="Operation",default="createContact")],defaults={"operation":"createContact"})
_reg('pipedrive','Pipedrive','crm-sales','#2b2b2b','Cloud',n8n_type='n8n-nodes-base.pipedrive',description='Pipedrive CRM',trigger=False,config_schema=[F_select("operation",[{"label":"Create Deal","value":"createDeal"},{"label":"Create Person","value":"createPerson"},{"label":"Get Deals","value":"getDeals"}],label="Operation",default="createDeal")],defaults={"operation":"createDeal"})
_reg('jira','Jira','project-management','#0052cc','Ticket',n8n_type='n8n-nodes-base.jira',description='Jira issues',trigger=False,config_schema=[F_select("operation",[{"label":"Search Issues","value":"search"},{"label":"Create Issue","value":"create"},{"label":"Get Issue","value":"get"},{"label":"Add Comment","value":"addComment"}],label="Operation",default="search")],defaults={"operation":"search"})
_reg('asana','Asana','project-management','#f06a6a','ClipboardList',n8n_type='n8n-nodes-base.asana',description='Asana tasks',trigger=False,config_schema=[F_select("operation",[{"label":"Create Task","value":"create"},{"label":"Get Task","value":"get"},{"label":"Search","value":"search"}],label="Operation",default="create")],defaults={"operation":"create"})
_reg('clickUp','ClickUp','project-management','#7b68ee','ClipboardList',n8n_type='n8n-nodes-base.clickUp',description='ClickUp tasks',trigger=False,config_schema=[F_select("operation",[{"label":"Create Task","value":"create"},{"label":"Get Task","value":"get"}],label="Operation",default="create")],defaults={"operation":"create"})
_reg('notion','Notion','project-management','#000000','BookOpen',n8n_type='n8n-nodes-base.notion',description='Notion API',trigger=False,config_schema=[F_select("operation",[{"label":"Create Page","value":"create"},{"label":"Query DB","value":"query"},{"label":"Get Page","value":"get"}],label="Operation",default="create")],defaults={"operation":"create"})
_reg('trello','Trello','project-management','#0079bf','ClipboardList',n8n_type='n8n-nodes-base.trello',description='Trello cards',trigger=False,config_schema=[F_select("operation",[{"label":"Create Card","value":"create"},{"label":"Get Card","value":"get"},{"label":"Search","value":"search"}],label="Operation",default="create")],defaults={"operation":"create"})
_reg('shopify','Shopify','ecommerce','#96bf48','ShoppingCart',n8n_type='n8n-nodes-base.shopify',description='Shopify store',trigger=False,config_schema=[F_select("operation",[{"label":"Get Orders","value":"getOrders"},{"label":"Get Products","value":"getProducts"}],label="Operation",default="getOrders")],defaults={"operation":"getOrders"})
_reg('woocommerce','WooCommerce','ecommerce','#96588a','ShoppingCart',n8n_type='n8n-nodes-base.wooCommerce',description='WooCommerce store',trigger=False,config_schema=[F_select("operation",[{"label":"Get Orders","value":"getOrders"},{"label":"Get Products","value":"getProducts"}],label="Operation",default="getOrders")],defaults={"operation":"getOrders"})
_reg('stripe','Stripe','ecommerce','#6772e5','CreditCard',n8n_type='n8n-nodes-base.stripe',description='Stripe payments',trigger=False,config_schema=[F_select("operation",[{"label":"Get Payments","value":"getPayments"},{"label":"Create Invoice","value":"createInvoice"},{"label":"Get Customers","value":"getCustomers"}],label="Operation",default="getPayments")],defaults={"operation":"getPayments"})
_reg('paypal','PayPal','ecommerce','#003087','CreditCard',n8n_type='n8n-nodes-base.paypal',description='PayPal payments',trigger=False,config_schema=[F_select("operation",[{"label":"Get Payments","value":"getPayments"},{"label":"Create Payout","value":"createPayout"}],label="Operation",default="getPayments")],defaults={"operation":"getPayments"})
_reg('aws','AWS','cloud-infra','#ff9900','Cloud',n8n_type='n8n-nodes-base.aws',description='AWS operations',trigger=False,config_schema=[F_select("service",[{"label":"S3","value":"s3"},{"label":"Lambda","value":"lambda"},{"label":"SES","value":"ses"},{"label":"SNS","value":"sns"}],label="Service",default="s3")],defaults={"service":"s3"})
_reg('google','Google','cloud-infra','#4285f4','Cloud',n8n_type='n8n-nodes-base.google',description='Google Workspace',trigger=False,config_schema=[F_select("service",[{"label":"Sheets","value":"sheets"},{"label":"Drive","value":"drive"},{"label":"Gmail","value":"gmail"},{"label":"Calendar","value":"calendar"}],label="Service",default="sheets")],defaults={"service":"sheets"})
_reg('cloudflare','Cloudflare','cloud-infra','#f38020','Cloud',n8n_type='n8n-nodes-base.cloudflare',description='Cloudflare',trigger=False,config_schema=[F_select("operation",[{"label":"Purge Cache","value":"purge"},{"label":"DNS Records","value":"dns"}],label="Operation",default="dns")],defaults={"operation":"dns"})
_reg('postgres','PostgreSQL','database','#336791','Database',n8n_type='n8n-nodes-base.postgres',description='PostgreSQL DB',trigger=False,config_schema=[F_select("operation",[{"label":"Execute Query","value":"execute"},{"label":"Insert","value":"insert"},{"label":"Update","value":"update"}],label="Operation",default="execute"),F_code("query",label="SQL",default="SELECT 1")],defaults={"operation":"execute","query":"SELECT 1"})
_reg('mysql','MySQL','database','#4479a1','Database',n8n_type='n8n-nodes-base.mySql',description='MySQL DB',trigger=False,config_schema=[F_select("operation",[{"label":"Execute Query","value":"execute"},{"label":"Insert","value":"insert"}],label="Operation",default="execute"),F_code("query",label="SQL",default="SELECT 1")],defaults={"operation":"execute","query":"SELECT 1"})
_reg('mongoDb','MongoDB','database','#47a248','Database',n8n_type='n8n-nodes-base.mongoDb',description='MongoDB',trigger=False,config_schema=[F_select("operation",[{"label":"Find","value":"find"},{"label":"Insert","value":"insert"},{"label":"Update","value":"update"},{"label":"Delete","value":"delete"}],label="Operation",default="find"),F_code("query",label="Query JSON",default="{}")],defaults={"operation":"find","query":"{}"})
_reg('redis','Redis','database','#dc382d','Database',n8n_type='n8n-nodes-base.redis',description='Redis',trigger=False,config_schema=[F_select("operation",[{"label":"Get","value":"get"},{"label":"Set","value":"set"},{"label":"Delete","value":"delete"}],label="Operation",default="get")],defaults={"operation":"get"})
_reg('elasticsearch','Elasticsearch','database','#005571','Search',n8n_type='n8n-nodes-base.elastic',description='Elasticsearch',trigger=False,config_schema=[F_select("operation",[{"label":"Search","value":"search"},{"label":"Index","value":"index"}],label="Operation",default="search")],defaults={"operation":"search"})
_reg('airtable','Airtable','database','#ffbf00','Grid3x3',n8n_type='n8n-nodes-base.airtable',description='Airtable',trigger=False,config_schema=[F_select("operation",[{"label":"List Records","value":"list"},{"label":"Create Record","value":"create"},{"label":"Update Record","value":"update"}],label="Operation",default="list")],defaults={"operation":"list"})
_reg('twitter','Twitter/X','social','#000000','Twitter',n8n_type='n8n-nodes-base.twitter',description='Twitter/X social',trigger=False,config_schema=[F_select("operation",[{"label":"Post Tweet","value":"post"},{"label":"Search","value":"search"},{"label":"Timeline","value":"timeline"}],label="Operation",default="post")],defaults={"operation":"post"})
_reg('linkedin','LinkedIn','social','#0077b5','Linkedin',n8n_type='n8n-nodes-base.linkedin',description='LinkedIn',trigger=False,config_schema=[F_select("operation",[{"label":"Post Update","value":"post"},{"label":"Company Info","value":"company"}],label="Operation",default="post")],defaults={"operation":"post"})
_reg('facebook','Facebook','social','#1877f2','Facebook',n8n_type='n8n-nodes-base.facebook',description='Facebook page',trigger=False,config_schema=[F_select("operation",[{"label":"Post to Page","value":"post"},{"label":"Get Insights","value":"insights"}],label="Operation",default="post")],defaults={"operation":"post"})
_reg('reddit','Reddit','social','#ff4500','MessageCircle',n8n_type='n8n-nodes-base.reddit',description='Reddit',trigger=False,config_schema=[F_select("operation",[{"label":"Get Posts","value":"getPosts"},{"label":"Post","value":"post"}],label="Operation",default="getPosts")],defaults={"operation":"getPosts"})
_reg('medium','Medium','social','#000000','BookOpen',n8n_type='n8n-nodes-base.medium',description='Medium publishing',trigger=False,config_schema=[F_select("operation",[{"label":"Create Post","value":"create"}],label="Operation",default="create")],defaults={"operation":"create"})
_reg('git','Git','developer-tools','#f05032','GitBranch',n8n_type='n8n-nodes-base.git',description='Git operations',trigger=False,config_schema=[F_select("operation",[{"label":"Status","value":"status"},{"label":"Commit","value":"commit"},{"label":"Push","value":"push"},{"label":"Pull","value":"pull"}],label="Operation",default="status")],defaults={"operation":"status"})
_reg('github','GitHub','developer-tools','#181717','Github',n8n_type='n8n-nodes-base.github',description='GitHub API',trigger=False,config_schema=[F_select("operation",[{"label":"List Issues","value":"listIssues"},{"label":"Create Issue","value":"createIssue"},{"label":"List PRs","value":"listPrs"},{"label":"Get Repo","value":"getRepo"}],label="Operation",default="listIssues")],defaults={"operation":"listIssues"})
_reg('gitlab','GitLab','developer-tools','#fc6d26','Gitlab',n8n_type='n8n-nodes-base.gitlab',description='GitLab API',trigger=False,config_schema=[F_select("operation",[{"label":"List Issues","value":"listIssues"},{"label":"Create Issue","value":"createIssue"}],label="Operation",default="listIssues")],defaults={"operation":"listIssues"})
_reg('docker','Docker','developer-tools','#2496ed','Container',n8n_type='n8n-nodes-base.docker',description='Docker containers',trigger=False,config_schema=[F_select("operation",[{"label":"List Containers","value":"list"},{"label":"Run Container","value":"run"},{"label":"Stop","value":"stop"}],label="Operation",default="list")],defaults={"operation":"list"})
_reg('httpRequest','HTTP Request','http-rest','#1e90ff','Globe',n8n_type='n8n-nodes-base.httpRequest',description='Make HTTP requests',trigger=False,config_schema=[F_string("url",label="URL",default=""),F_select("method",[{"label":"GET","value":"GET"},{"label":"POST","value":"POST"},{"label":"PUT","value":"PUT"},{"label":"DELETE","value":"DELETE"}],label="Method",default="GET"),F_json("headers",label="Headers",default="{}"),F_json("body",label="Body",default="{}")],defaults={"url":"","method":"GET","headers":"{}","body":"{}"})
_reg('graphql','GraphQL','http-rest','#e535ab','Globe',n8n_type='n8n-nodes-base.graphql',description='GraphQL queries',trigger=False,config_schema=[F_string("endpoint",label="Endpoint",default=""),F_code("query",label="Query",default=""),F_json("variables",label="Variables",default="{}")],defaults={"endpoint":"","query":"","variables":"{}"})
_reg('dateTime','Date & Time','utilities','#747d8c','Calendar',n8n_type='n8n-nodes-base.dateTime',description='Date/time utils',trigger=False,config_schema=[F_select("operation",[{"label":"Current Time","value":"now"},{"label":"Format","value":"format"},{"label":"Add Time","value":"add"}],label="Operation",default="now")],defaults={"operation":"now"})
_reg('uuid','UUID','utilities','#747d8c','Fingerprint',n8n_type='n8n-nodes-base.uuid',description='Generate UUIDs',trigger=False,config_schema=[F_select("version",[{"label":"UUID v4","value":"v4"}],label="Version",default="v4"),F_number("count",label="Count",default=1)],defaults={"version":"v4","count":1})
_reg('html','HTML','utilities','#747d8c','Code',n8n_type='n8n-nodes-base.html',description='HTML templates',trigger=False,config_schema=[F_code("template",label="HTML",default="<html></html>")],defaults={"template":"<html></html>"})
_reg('jwt','JWT','utilities','#747d8c','Lock',n8n_type='n8n-nodes-base.jwt',description='Encode/decode JWT',trigger=False,config_schema=[F_select("operation",[{"label":"Encode","value":"encode"},{"label":"Decode","value":"decode"},{"label":"Verify","value":"verify"}],label="Operation",default="encode")],defaults={"operation":"encode"})

# ── Credentials Store ──
class CredentialStore:
    def __init__(self):
        self._credentials: dict[str, dict] = {}
        self._load()

    def _path(self) -> str:
        os.makedirs(_WORKFLOWS_DIR, exist_ok=True)
        return os.path.join(_WORKFLOWS_DIR, "credentials.json")

    def _load(self) -> None:
        path = self._path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    self._credentials = json.load(f)
            except Exception:
                self._credentials = {}

    def _save(self) -> None:
        with open(self._path(), "w") as f:
            json.dump(self._credentials, f, indent=2)

    def list(self) -> list[dict]:
        return [{"id":k,"name":v.get("name",""),"type":v.get("type","")} for k,v in self._credentials.items()]

    def get(self, cred_id: str) -> dict | None:
        return self._credentials.get(cred_id)

    def create(self, name: str, cred_type: str, data: dict) -> dict:
        cid = uuid.uuid4().hex[:12]
        entry = {"id":cid,"name":name,"type":cred_type,"data":data,"created_at":time.time()}
        self._credentials[cid] = entry
        self._save()
        return entry

    def update(self, cred_id: str, data: dict) -> dict | None:
        if cred_id not in self._credentials:
            return None
        self._credentials[cred_id]["data"].update(data)
        self._save()
        return self._credentials[cred_id]

    def delete(self, cred_id: str) -> bool:
        if cred_id not in self._credentials:
            return False
        del self._credentials[cred_id]
        self._save()
        return True

# ── Data Models ──
class WorkflowNode:
    def __init__(self,node_type,label,config=None,position=None,
               node_id=None,credentials=None,notes=""):
        self.id = node_id or uuid.uuid4().hex[:8]
        self.type = node_type
        self.label = label
        self.config = config or {}
        self.position = position or {"x":0,"y":0}
        self.credentials = credentials
        self.notes = notes

    def to_dict(self) -> dict:
        d = {"id":self.id,"type":self.type,"label":self.label,
             "config":self.config,"position":self.position}
        if self.credentials: d["credentials"] = self.credentials
        if self.notes: d["notes"] = self.notes
        return d

    @classmethod
    def from_dict(cls, d: dict) -> WorkflowNode:
        return cls(node_id=d.get("id"),node_type=d["type"],
            label=d.get("label",""),config=d.get("config",{}),
            position=d.get("position",{"x":0,"y":0}),
            credentials=d.get("credentials"),notes=d.get("notes",""))

class WorkflowEdge:
    def __init__(self,source,target,edge_id=None,label="",
               sourceHandle="",targetHandle=""):
        self.id = edge_id or uuid.uuid4().hex[:8]
        self.source = source
        self.target = target
        self.label = label
        self.sourceHandle = sourceHandle
        self.targetHandle = targetHandle

    def to_dict(self) -> dict:
        d = {"id":self.id,"source":self.source,"target":self.target,"label":self.label}
        if self.sourceHandle: d["sourceHandle"] = self.sourceHandle
        if self.targetHandle: d["targetHandle"] = self.targetHandle
        return d

    @classmethod
    def from_dict(cls, d: dict) -> WorkflowEdge:
        return cls(edge_id=d.get("id"),source=d["source"],target=d["target"],
            label=d.get("label",""),sourceHandle=d.get("sourceHandle",""),
            targetHandle=d.get("targetHandle",""))

class Workflow:
    def __init__(self,name,description="",category="custom",
               workflow_id=None,created_at=None,updated_at=None,
               tags=None,settings=None):
        self.id = workflow_id or uuid.uuid4().hex[:12]
        self.name = name
        self.description = description
        self.category = category if category in WORKFLOW_CATEGORIES else "custom"
        self.nodes: list[WorkflowNode] = []
        self.edges: list[WorkflowEdge] = []
        self.tags = tags or []
        self.settings = settings or {"executionOrder":"v1","timezone":"UTC"}
        self.created_at = created_at or time.time()
        self.updated_at = updated_at or time.time()

    def add_node(self, node: WorkflowNode) -> str:
        self.nodes.append(node)
        self.updated_at = time.time()
        return node.id

    def update_node(self, node_id, **kwargs):
        for node in self.nodes:
            if node.id == node_id:
                for k,v in kwargs.items():
                    if isinstance(v,dict) and k == "config":
                        node.config.update(v)
                    elif hasattr(node,k):
                        setattr(node,k,v)
                self.updated_at = time.time()
                return node
        return None

    def remove_node(self, node_id) -> bool:
        self.nodes = [n for n in self.nodes if n.id != node_id]
        self.edges = [e for e in self.edges if e.source != node_id and e.target != node_id]
        self.updated_at = time.time()
        return True

    def add_edge(self, edge: WorkflowEdge) -> str:
        self.edges.append(edge)
        self.updated_at = time.time()
        return edge.id

    def remove_edge(self, edge_id) -> bool:
        self.edges = [e for e in self.edges if e.id != edge_id]
        self.updated_at = time.time()
        return True

    def to_dict(self) -> dict:
        return {
            "id":self.id,"name":self.name,"description":self.description,
            "category":self.category,
            "nodes":[n.to_dict() for n in self.nodes],
            "edges":[e.to_dict() for e in self.edges],
            "tags":self.tags,"settings":self.settings,
            "created_at":self.created_at,"updated_at":self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Workflow:
        wf = cls(name=d["name"],description=d.get("description",""),
            category=d.get("category","custom"),workflow_id=d.get("id"),
            created_at=d.get("created_at"),updated_at=d.get("updated_at"),
            tags=d.get("tags",[]),settings=d.get("settings",{}))
        wf.nodes = [WorkflowNode.from_dict(n) for n in d.get("nodes",[])]
        wf.edges = [WorkflowEdge.from_dict(e) for e in d.get("edges",[])]
        return wf

class WorkflowExecutionError(Exception):
    pass

N8N_TEMPLATES: list[dict] = []

def _n(nid, typ, label, config, x, y):
    return {"id": nid, "type": typ, "label": label, "config": config, "position": {"x": x, "y": y}}

def _e(eid, src, tgt):
    return {"id": eid, "source": src, "target": tgt}

_N8N_TEMPLATES_LOADED = False
def _ensure_templates():
    global _N8N_TEMPLATES_LOADED, N8N_TEMPLATES
    if not _N8N_TEMPLATES_LOADED:
        N8N_TEMPLATES.clear()
        N8N_TEMPLATES.extend(_load_templates())
        _N8N_TEMPLATES_LOADED = True

def _load_templates():
    import json, os
    p = os.path.join(_WORKFLOWS_DIR, "builtin_templates.json")
    if os.path.exists(p):
        try:
            with open(p) as f:
                return json.load(f)
        except:
            pass
    return []

class WorkflowStore:
    def __init__(self):
        self._workflows: list[Workflow] = []
        self._load()

    def _path(self, name: str) -> str:
        os.makedirs(_WORKFLOWS_DIR, exist_ok=True)
        return os.path.join(_WORKFLOWS_DIR, name)

    def _templates_path(self) -> str:
        return self._path("templates.json")

    def _load(self) -> None:
        path = self._path("workflows.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    self._workflows = [Workflow.from_dict(d) for d in json.load(f)]
            except Exception:
                self._workflows = []

    def _save(self) -> None:
        with open(self._path("workflows.json"), "w") as f:
            json.dump([w.to_dict() for w in self._workflows], f, indent=2)

    def create(self, name, description="", category="custom"):
        wf = Workflow(name=name, description=description, category=category)
        self._workflows.append(wf)
        self._save()
        return wf

    def list(self, category=None):
        if category:
            return [w for w in self._workflows if w.category == category]
        return sorted(self._workflows, key=lambda w: w.updated_at, reverse=True)

    def get(self, workflow_id):
        for w in self._workflows:
            if w.id == workflow_id:
                return w
        return None

    def update(self, workflow_id, **kwargs):
        wf = self.get(workflow_id)
        if not wf:
            return None
        for k, v in kwargs.items():
            if hasattr(wf, k):
                setattr(wf, k, v)
        wf.updated_at = time.time()
        self._save()
        return wf

    def delete(self, workflow_id):
        for i, w in enumerate(self._workflows):
            if w.id == workflow_id:
                self._workflows.pop(i)
                self._save()
                return True
        return False

    # ── n8n Integration ──

    def to_n8n_json(self, workflow_id):
        wf = self.get(workflow_id)
        if not wf:
            return None
        n8n_nodes = []
        n8n_connections = {}
        for node in wf.nodes:
            nid = node.id
            nt = NODE_TYPE_MAP.get(node.type, "n8n-nodes-base." + node.type)
            n8n_nodes.append({
                "id": nid, "name": node.label, "type": nt,
                "typeVersion": 1,
                "position": [node.position.get("x", 0), node.position.get("y", 0)],
                "parameters": node.config,
            })
            n8n_connections[nid] = {"main": [[]]}
        edge_map = {}
        for e in wf.edges:
            edge_map.setdefault(e.source, []).append(e.target)
        for src, targets in edge_map.items():
            if src in n8n_connections:
                for tgt in targets:
                    n8n_connections[src]["main"][0].append({"node": tgt, "type": "main", "index": 0})
        for node in n8n_nodes:
            nid = node["id"]
            node["connections"] = n8n_connections.get(nid, {"main": [[]]})
        return {
            "name": wf.name, "nodes": n8n_nodes,
            "connections": {nid: c for nid, c in n8n_connections.items() if c["main"][0]},
            "settings": {"executionOrder": "v1"}, "id": wf.id, "tags": [],
        }

    def from_n8n_json(self, n8n_data, name=None):
        wf = Workflow(name=name or n8n_data.get("name", "Imported n8n"), category="custom")
        id_map = {}
        for n in n8n_data.get("nodes", []):
            orig_id = n.get("id", uuid.uuid4().hex[:8])
            new_id = uuid.uuid4().hex[:8]
            id_map[orig_id] = new_id
            nt = REVERSE_NODE_MAP.get(n.get("type", ""), "")
            if not nt:
                t = n.get("type", "")
                nt = t.replace("n8n-nodes-base.", "") if t.startswith("n8n-nodes-base.") else "action"
            wf.add_node(WorkflowNode(
                node_id=new_id, node_type=nt,
                label=n.get("name", "Node"), config=n.get("parameters", {}),
                position={"x": n.get("position", [0, 0])[0], "y": n.get("position", [0, 0])[1]},
            ))
        for n in n8n_data.get("nodes", []):
            orig_id = n.get("id", "")
            for conn_list in n.get("connections", {}).get("main", []):
                for conn in conn_list:
                    target_orig = conn.get("node", "")
                    if orig_id in id_map and target_orig in id_map:
                        wf.add_edge(WorkflowEdge(source=id_map[orig_id], target=id_map[target_orig]))
        return wf

    def get_n8n_templates(self, category=None, query="", offset=0, limit=50):
        _ensure_templates()
        templates = list(N8N_TEMPLATES)
        custom = self._load_custom_templates()
        templates.extend(custom)
        if category:
            templates = [t for t in templates if t.get("category") == category]
        if query:
            q = query.lower()
            templates = [
                t for t in templates
                if q in t.get("name", "").lower()
                or q in t.get("description", "").lower()
                or any(q in tag.lower() for tag in t.get("tags", []))
            ]
        total = len(templates)
        return {"templates": templates[offset:offset + limit], "total": total, "offset": offset, "limit": limit}

    def _load_custom_templates(self):
        path = self._templates_path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save_custom_templates(self, templates):
        with open(self._templates_path(), "w") as f:
            json.dump(templates, f, indent=2)

    def save_as_template(self, workflow_id, tags=None):
        wf = self.get(workflow_id)
        if not wf:
            return None
        tmpl = {
            "id": "custom-" + uuid.uuid4().hex[:8],
            "name": wf.name, "description": wf.description,
            "category": wf.category, "tags": tags or [],
            "workflow": {
                "name": wf.name,
                "nodes": [n.to_dict() for n in wf.nodes],
                "edges": [e.to_dict() for e in wf.edges],
            },
        }
        custom = self._load_custom_templates()
        custom.append(tmpl)
        self._save_custom_templates(custom)
        return tmpl

    def create_custom_template(self, name, description, category, node_types, tags=None):
        nodes = []
        edges = []
        for i, nt in enumerate(node_types):
            info = NODE_REGISTRY.get(nt, {"label": nt, "icon": "template", "color": "#64748b"})
            nid = uuid.uuid4().hex[:8]
            nodes.append({
                "id": nid, "type": nt, "label": info.get("label", nt),
                "config": {}, "position": {"x": 50, "y": i * 120 + 40},
            })
            if i > 0:
                edges.append({"id": uuid.uuid4().hex[:8], "source": nodes[i-1]["id"], "target": nid})
        tmpl = {
            "id": "custom-" + uuid.uuid4().hex[:8],
            "name": name, "description": description,
            "category": category, "tags": tags or [],
            "workflow": {"name": name, "nodes": nodes, "edges": edges},
        }
        custom = self._load_custom_templates()
        custom.append(tmpl)
        self._save_custom_templates(custom)
        return tmpl

    def delete_custom_template(self, template_id):
        custom = self._load_custom_templates()
        before = len(custom)
        custom = [t for t in custom if t["id"] != template_id]
        if len(custom) == before:
            return False
        self._save_custom_templates(custom)
        return True

    def import_n8n_template(self, template_id):
        _ensure_templates()
        all_t = list(N8N_TEMPLATES) + self._load_custom_templates()
        tmpl = next((t for t in all_t if t["id"] == template_id), None)
        if not tmpl:
            return None
        wf = Workflow(name=tmpl["name"], description=tmpl.get("description", ""), category=tmpl.get("category", "custom"))
        id_map = {}
        wf_data = tmpl.get("workflow", {})
        if not wf_data.get("nodes"):
            wf_data = tmpl
        for n in wf_data.get("nodes", []):
            orig_id = n["id"]
            new_id = uuid.uuid4().hex[:8]
            id_map[orig_id] = new_id
            wf.add_node(WorkflowNode(
                node_id=new_id, node_type=n["type"], label=n.get("label", ""),
                config=n.get("config", {}), position=n.get("position", {"x": 0, "y": 0}),
            ))
        for e in wf_data.get("edges", []):
            if e["source"] in id_map and e["target"] in id_map:
                wf.add_edge(WorkflowEdge(source=id_map[e["source"]], target=id_map[e["target"]]))
        self._workflows.append(wf)
        self._save()
        return wf

    async def check_n8n_health(self):
        return {"online": False, "note": "Use export/import instead"}

    async def push_to_n8n(self, workflow_id):
        return {"success": False, "error": "Live push not available"}

    async def execute_on_n8n(self, workflow_id):
        return {"success": False, "error": "Live execution not available"}

    async def install_n8n(self):
        return {"success": False, "error": "Install separately with: npm install -g n8n"}

    async def get_n8n_workflows(self):
        return {"success": False, "error": "Remote n8n workflows not available"}

    # ── Workflow Execution Engine ──

    def execute_workflow(self, workflow_id, payload=None):
        wf = self.get(workflow_id)
        if not wf:
            return {"success": False, "error": "Workflow not found"}
        if not wf.nodes:
            return {"success": False, "error": "Workflow has no nodes"}

        triggers = [n for n in wf.nodes if NODE_REGISTRY.get(n.type, {}).get("trigger", False)]
        if not triggers:
            return {"success": False, "error": "No trigger node found"}

        data = payload or {}
        outputs = {}
        visited = set()
        errors = []

        edge_map = {}
        for e in wf.edges:
            edge_map.setdefault(e.source, []).append(e.target)

        def get_node_label(nid):
            n = next((x for x in wf.nodes if x.id == nid), None)
            return n.label if n else nid

        def follow(node_id, input_data):
            if node_id in visited:
                return
            visited.add(node_id)
            node = next((n for n in wf.nodes if n.id == node_id), None)
            if not node:
                return
            try:
                result = _execute_node(node, input_data)
            except WorkflowExecutionError as e:
                errors.append(f"[{get_node_label(node_id)}] {e}")
                outputs[node_id] = {"status": "error", "error": str(e), "type": node.type, "label": node.label}
                return
            except Exception as e:
                errors.append(f"[{get_node_label(node_id)}] Unexpected: {e}")
                outputs[node_id] = {"status": "error", "error": str(e), "type": node.type, "label": node.label}
                return
            outputs[node_id] = {"status": "ok", "output": result, "type": node.type, "label": node.label}
            if node.type == "if":
                truthy = bool(result.get("result", False))
                targets = edge_map.get(node_id, [])
                if truthy and targets:
                    follow(targets[0], result)
                elif not truthy and len(targets) > 1:
                    follow(targets[1], result)
            elif node.type == "wait":
                import asyncio
                seconds = int(node.config.get("amount", 1))
                unit = node.config.get("unit", "seconds")
                if unit == "minutes":
                    seconds *= 60
                elif unit == "hours":
                    seconds *= 3600
                try:
                    asyncio.run(asyncio.sleep(seconds))
                except RuntimeError:
                    time.sleep(seconds)
                for t in edge_map.get(node_id, []):
                    follow(t, result)
            elif node.type == "loop":
                count = int(node.config.get("count", 5))
                for i in range(count):
                    for t in edge_map.get(node_id, []):
                        follow(t, {**result, "_loopIndex": i})
            else:
                for t in edge_map.get(node_id, []):
                    follow(t, result)

        for trigger in triggers:
            follow(trigger.id, data)

        return {
            "success": len(errors) == 0,
            "errors": errors,
            "outputs": outputs,
            "node_count": len(visited),
            "total_nodes": len(wf.nodes),
        }


# ── Execution Helpers ──

def _execute_node(node, input_data):
    config = _resolve_deep(node.config, input_data)

    if node.type in ("webhook", "manual", "form"):
        return {"triggered": True, "payload": input_data}

    if node.type == "schedule":
        return {"triggered": True, "cron": config.get("cron", ""), "payload": input_data}

    if node.type == "webhookListener":
        return {"responded": True, "body": config.get("body", "{}"), "type": config.get("respondWith", "json")}

    if node.type in ("errorTrigger", "emailTrigger", "rssTrigger"):
        return {"triggered": True, "payload": input_data}

    if node.type == "httpRequest":
        url = config.get("url", "")
        method = config.get("method", "GET").upper()
        headers = config.get("headers", "{}")
        body = config.get("body", None)
        try:
            if isinstance(headers, str):
                headers = json.loads(headers) if headers.strip() else {}
            if isinstance(body, str):
                try:
                    body = json.loads(body) if body.strip() else None
                except Exception:
                    pass
            client_kwargs = {"timeout": 15, "headers": headers}
            if body is not None:
                client_kwargs["json"] = body
            base = os.environ.get("LUMINA_HOST", "http://localhost:8000")
            if url.startswith("/"):
                url = base.rstrip("/") + url
            r = httpx.request(method, url, **client_kwargs)
            return {"status": r.status_code, "body": r.text[:5000], "headers": dict(r.headers)}
        except Exception as e:
            raise WorkflowExecutionError(f"HTTP request failed: {e}") from e

    if node.type in ("emailSend", "emailReadImap", "slack", "discord", "telegram", "twilio", "whatsApp"):
        return {"sent": True, "config": config}

    if node.type in ("llm", "agent"):
        return {"ai": True, "provider": config.get("provider", "openai"), "model": config.get("model", ""), "messages": config.get("messages", "[]")}

    if node.type in ("vectorStore", "embeddings", "tool", "memory", "textSplitter", "documentLoader", "outputParser", "aiTransform"):
        return {"ai": True, "type": node.type, "config": config}

    if node.type == "if":
        return _eval_condition(config, input_data)

    if node.type in ("salesforce", "hubspot", "pipedrive", "shopify", "woocommerce", "stripe", "paypal",
                     "jira", "asana", "clickUp", "notion", "trello",
                     "aws", "google", "cloudflare",
                     "postgres", "mysql", "mongoDb", "redis", "elasticsearch", "airtable",
                     "twitter", "linkedin", "facebook", "reddit", "medium",
                     "git", "github", "gitlab", "docker"):
        return {"integration": True, "type": node.type, "config": config}

    if node.type == "set":
        values = config.get("values", "{}")
        if isinstance(values, str):
            try:
                values = json.loads(values) if values.strip() else {}
            except Exception:
                values = {}
        return {"set": True, "values": values, "mode": config.get("mode", "set")}

    if node.type == "code":
        return {"executed": True, "language": config.get("language", "javascript"), "source": config.get("source", "")}

    if node.type in ("function", "itemLists", "compareDatasets", "renameKeys", "transform"):
        return {"transform": True, "type": node.type, "config": config}

    if node.type in ("compression", "crypto", "spreadsheetFile", "files", "readPdf"):
        return {"file": True, "type": node.type, "config": config}

    if node.type in ("dateTime", "uuid", "html", "jwt"):
        return {"utility": True, "type": node.type, "config": config}

    if node.type in ("graphql", "noOp", "stickyNote", "executeWorkflow", "switch", "merge", "splitInBatches", "loop"):
        return {"executed": True, "type": node.type, "config": config}

    if node.type == "stopAndError":
        raise WorkflowExecutionError(config.get("message", "Workflow stopped"))

    if node.type in ("wait", "delay"):
        return {"delayed": True, "duration": config}

    return {"executed": True, "type": node.type, "config": config}


def _eval_condition(config, input_data):
    comparison = config.get("comparison", "eq")
    value1 = config.get("value1", "")
    value2 = config.get("value2", "")
    v1 = _resolve_value(value1, input_data)
    v2 = _resolve_value(value2, input_data) if value2 else None
    if comparison == "exists":
        result = v1 is not None and v1 != ""
    elif comparison == "isEmpty":
        result = v1 is None or v1 == ""
    elif comparison == "eq":
        result = str(v1) == str(v2)
    elif comparison == "neq":
        result = str(v1) != str(v2)
    elif comparison == "gt":
        try:
            result = float(v1) > float(v2)
        except (TypeError, ValueError):
            result = False
    elif comparison == "lt":
        try:
            result = float(v1) < float(v2)
        except (TypeError, ValueError):
            result = False
    elif comparison == "contains":
        result = str(v2) in str(v1) if v2 else False
    elif comparison == "startsWith":
        result = str(v1).startswith(str(v2)) if v2 else False
    elif comparison == "endsWith":
        result = str(v1).endswith(str(v2)) if v2 else False
    else:
        result = bool(v1)
    return {"result": result, "value1": v1, "value2": v2, "comparison": comparison}


def _resolve_value(expr, data):
    if isinstance(expr, str) and "{{" in expr:
        return _resolve_template(expr, data)
    return expr


def _resolve_template(template, data):
    def replacer(m):
        expr = m.group(1).strip()
        if expr == "$json":
            return json.dumps(data)
        if expr == "$now":
            return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        keys = expr.replace("$json.", "").split(".")
        val = data
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k, "")
            elif isinstance(val, list) and k.isdigit():
                try:
                    val = val[int(k)]
                except (IndexError, ValueError):
                    val = ""
            else:
                val = ""
                break
        return str(val) if val is not None else ""
    return re.sub(r"\{\{\s*([^}]+)\s*\}\}", replacer, template)


def _resolve_deep(cfg, data):
    if isinstance(cfg, str):
        return _resolve_template(cfg, data) if "{{" in cfg else cfg
    if isinstance(cfg, dict):
        return {k: _resolve_deep(v, data) for k, v in cfg.items()}
    if isinstance(cfg, list):
        return [_resolve_deep(v, data) for v in cfg]
    return cfg


credential_store = CredentialStore()
workflow_store = WorkflowStore()
