"""
Usage: python arcs_anchor_mentions.py key_file.conll response_file.conll
"""

import re,sys,pdb

"""settings"""

#noun_pos_tags=['NN','NE']                                              #German
#pronoun_pos_tags=['PPER','PPOSAT','PRELS']                               #German
noun_pos_tags=['NN','NNS','NNP','NNPS']                                 #English
pronoun_pos_tags=['PRP','PRP$']                                         #English
pos_index=4                                                                 #list index of the POS tag

all_key=re.split('#end document[^\n]*',open(sys.argv[1],'r').read())    #split documents at lines starting with "#end document", consume everything except newline
all_res=re.split('#end document[^\n]*',open(sys.argv[2],'r').read())
if re.match('\n+',all_key[-1]): del all_key[-1]                         #splitting artefacts
if re.match('\n+',all_res[-1]): del all_res[-1]

if len(all_key)!=len(all_res): 
    print 'Key and response file do not have the same number of documents.'
    pdb.set_trace()

evaluation={'tp':0,'fn':0,'fp':0}
evaluation_entity_detection={'tp':0,'fn':0,'fp':0}
evaluation_ne={}
evaluation_ne_doc={}
evaluation_entity_detection_ne={}
evaluation_entity_detection_ne_doc={}

tp=fp=ftp=fn=0

doc_ids=[]
docs={'key':{},'res':{}}

""" gather coreference annotation from the key and response files """

#load the documents from the key
for doc in all_key:
    if not doc.lstrip().startswith('#begin'):
        print "No '#begin document...' at key document beginning"       #every doc should start with this
        pdb.set_trace()
    else:
        key=re.sub('\n{3,}','\n\n',doc)                                 #normalize multiple newlines
        key=key.lstrip().split('\n')                                    #lstrip to remove newlines at document beginning    
        docid=re.search('#begin document ([^\n]+)',key[0]).group(1)     #document id
        docs['key'][docid]=key
        doc_ids.append(docid)

#load the documents from the response
for doc in all_res:
    if not doc.lstrip().startswith('#begin'):
        print "No '#begin document...' at response document beginning"
        pdb.set_trace()
    else:
        res=re.sub('\n{3,}','\n\n',doc)
        res=res.lstrip().split('\n')
        docid=re.search('#begin document ([^\n]+)',res[0]).group(1)
        docs['res'][docid]=res
        if not docid in doc_ids: doc_ids.append(docid)

#process each document        
for doc in doc_ids:                                                     #for each document name in the key
    if not doc in docs['key']:
        print doc,'is in the response, but not in the key. Enter c to continue ommiting the document or q to quit...'
        pdb.set_trace()
        continue                                                        #ommit documents not in key/res
    
    if not doc in docs['res']: 
        print doc,'is in the key but not in the response. Enter c to continue ommiting the document or q to quit...'
        pdb.set_trace()
        continue                                                        #ommit documents not in key/res
        
    key=docs['key'][doc]
    res=docs['res'][doc]
    if len(key)!=len(res): 
        print 'Key and response document have not the same number of lines. Key has',len(key),'lines. The response has',len(res),'lines.'
        pdb.set_trace()
    
    """ gather key sets """
    key_sets={}
    for line in key:            
        if line.startswith('#'):
            print line
            sent_nr=0
            token_nr=1                
        elif line=='': 
            sent_nr+=1
            token_nr=1            
        elif not line.endswith('-') and not line.endswith('_'):         #we have coreference information
            line=re.split(' +|\t',line)                                 #allow both mutliple spaces and tab separation for robustness
            ids=line[-1].split('|')                                     #split coref information                
            for id in ids:                
                if id.startswith('(') and id.endswith(')'):             #single word term
                    id=re.search('\d+',id).group()
                    if line[10]!='*': 
                        if re.match('\((\w+)\)',line[10]):ne_type_local=re.search('\((\w+)\)',line[10]).group(1)    #named entity type
                    else: ne_type_local='*'
                    if id in key_sets: key_sets[id].append([sent_nr,token_nr,token_nr,line[pos_index],ne_type_local])
                    else: key_sets[id]=[[sent_nr,token_nr,token_nr,line[pos_index],ne_type_local]]              
                elif id.startswith('('):                                #start of multiple word term
                    id=re.search('\d+',id).group()
                    if line[10]!='*' and not line[10].endswith(')'): ne_type_local=re.search('\((\w+)',line[10]).group(1)   #named entity type must span the whole markable
                    else: ne_type_local='*'
                    if id in key_sets: key_sets[id].append([sent_nr,token_nr,ne_type_local])
                    else: key_sets[id]=[[sent_nr,token_nr,ne_type_local]]              
                elif id.endswith(')'):                                  #end of multiple word term
                    id=re.search('\d+',id).group()
                    for m in key_sets[id]:
                        if len(m)==3: 
                            m.insert(2,token_nr)
                            if not line[10].endswith(')'): m[-1]='*'
                            break                      
            token_nr+=1            
        else: token_nr+=1

    """ gather response sets """
    res_sets={}
    for line in res:            
        if line.startswith('#'): 
            sent_nr=0
            token_nr=1                
        elif line=='': 
            sent_nr+=1
            token_nr=1
        elif not line.endswith('-') and not line.endswith('_'):         #we have coreference information
            line=re.split(' +|\t',line)                                 #allow both mutliple spaces and tab separation for robustness
            ids=line[-1].split('|')                                     #split coref information                
            for id in ids:                
                if id.startswith('(') and id.endswith(')'):             #single word term
                    id=re.search('\d+',id).group()
                    if line[10]!='*': 
                        if re.match('\((\w+)\)',line[10]):ne_type_local=re.search('\((\w+)\)',line[10]).group(1)
                    else: ne_type_local='*'
                    if id in res_sets: res_sets[id].append([sent_nr,token_nr,token_nr,line[pos_index],ne_type_local])
                    else: res_sets[id]=[[sent_nr,token_nr,token_nr,line[pos_index],ne_type_local]]              
                elif id.startswith('('):                                #start of multiple word term
                    id=re.search('\d+',id).group()
                    if line[10]!='*' and not line[10].endswith(')'): ne_type_local=re.search('\((\w+)',line[10]).group(1)
                    else: ne_type_local='*'
                    if id in res_sets: res_sets[id].append([sent_nr,token_nr,ne_type_local])
                    else: res_sets[id]=[[sent_nr,token_nr,ne_type_local]]              
                elif id.endswith(')'):                                  #end of multiple word term
                    id=re.search('\d+',id).group()
                    for m in res_sets[id]:
                        if len(m)==3: 
                            m.insert(2,token_nr)
                            if not line[10].endswith(')'): m[-1]='*'
                            break                          
            token_nr+=1            
        else: token_nr+=1            
    
    key_sets=sorted(key_sets.values())                                  #turn key and response into sorted list of lists
    res_sets=sorted(res_sets.values())
        
    """ start comparing key and response sets on mention basis """
    doc_tp=doc_fp=doc_ftp=doc_fn=0
    evaluation_doc={'tp':0,'fn':0,'fp':0}
    evaluation_entity_detection_doc={'tp':0,'fn':0,'fp':0}

    
    #Recall: we compare key to response mentions   
    for key_set in key_sets:                                            #for every cset in the key            
        if len(key_set)==1: continue                                    #we don't handle singletons

        #determine the anchor mention
        try: key_m=next(m for m in key_set if len(m)==4 or m[3] in noun_pos_tags)    #prefer the first long NP to be the anchor mention
        except StopIteration:                                           #there is no anchor mention in the set
            break_here=False
            for c in res_sets:
                if break_here: break
                for tm in key_set:
                    if [m for m in c if tm[:3]==m[:3]]!=[]:             #the key mention is in the response set
                        res_sets.remove(c)                              #remove the set from the response
                        break_here=True
                        break                               
            continue

        if key_m[-1]=='*' and len(set([m[-1] for m in key_set]))==2:    #if there is ONE(!) NE tag other than '*', take it
            ne_tag=next(m[-1] for m in key_set if m[-1]!='*') 
            key_m[-1]=ne_tag            
        
        #determine the response chain
        res_set=[]
        for c in res_sets:
            if [m for m in c if m[:3]==key_m[:3]]!=[]:                  #the anchor mention is in the set
                if not c in res_set: res_set.append(c)
        if len(res_set)>1:                                              #the anchor is in multiple response sets
            print 'Key mention',key_m,'\n is in multiple response sets:\n',res_sets 
            pdb.set_trace()    
        elif res_set==[]:                                               #no response chain contains the anchor mention
            evaluation_entity_detection['fn']+=1
            evaluation_entity_detection_doc['fn']+=1
            if evaluation_entity_detection_ne.has_key(key_m[-1]): evaluation_entity_detection_ne[key_m[-1]]['fn']+=1
            else: evaluation_entity_detection_ne[key_m[-1]]={'tp':0,'fp':0,'fn':1}
        else:                                                           #we have a response set containing the anchor
            evaluation_entity_detection['tp']+=1                        #the anchor mention is in a res set -> 1 true positive for entity detection
            evaluation_entity_detection_doc['tp']+=1
            if evaluation_entity_detection_ne.has_key(key_m[-1]): evaluation_entity_detection_ne[key_m[-1]]['tp']+=1
            else: evaluation_entity_detection_ne[key_m[-1]]={'tp':1,'fp':0,'fn':0}
            
            #Entity Mention Recall: cont how many references to the anchor have been found
            for tm in key_set:                                          
                if [m for m in res_set[0] if m[:3]==tm[:3]]!=[]:
                    tp+=1
                    doc_tp+=1
                    evaluation['tp']+=1
                    evaluation_doc['tp']+=1
                    if evaluation_ne.has_key(key_m[-1]): evaluation_ne[key_m[-1]]['tp']+=1
                    else: evaluation_ne[key_m[-1]]={'tp':1,'fp':0,'fn':0}                    
                else:
                    fn+=1
                    doc_fn+=1
                    evaluation['fn']+=1
                    evaluation_doc['fn']+=1
                    if evaluation_ne.has_key(key_m[-1]): evaluation_ne[key_m[-1]]['fn']+=1
                    else: evaluation_ne[key_m[-1]]={'tp':0,'fp':0,'fn':1}                                        
            
            #Entity Mention Precision: count of response mentions not in the key set, i.e. false positives
            fp_set=len([m for m in res_set[0] if [n for n in key_set if n[:3]==m[:3]]==[]])
            fp+=fp_set
            doc_fp+=fp_set
            evaluation['fp']+=fp_set
            evaluation_doc['fp']+=fp_set
            if evaluation_ne.has_key(key_m[-1]): evaluation_ne[key_m[-1]]['fp']+=fp_set
            else: evaluation_ne[key_m[-1]]={'tp':0,'fp':fp_set,'fn':0}                                
            #remove the found set from the response. we then can check if there are unmatched response sets left -> Entity Detection Precision
            res_sets.remove(res_set[0])

    #some response sets were not matched -> they are spurios entities, add to false positives in Entity Detection            
    if not res_sets==[]:
        fp_spurious=0
        for cset in res_sets:
            if not len(cset)==1: 
                try: 
                    res_m=next(m for m in cset if len(m)==4 or m[3] in noun_pos_tags)               #find a nominal mentions
                    fp_spurious+=len(cset)
                    if evaluation_entity_detection_ne.has_key(res_m[-1]): evaluation_entity_detection_ne[res_m[-1]]['fp']+=1
                    else: evaluation_entity_detection_ne[res_m[-1]]={'tp':0,'fp':1,'fn':0}
                    if res_m[-1]=='*' and len(set([m[-1] for m in cset]))==2:                       #if there is ONE(!) NE tag other than '*', take it
                        ne_tag=next(m[-1] for m in cset if m[-1]!='*') 
                        res_m[-1]=ne_tag            
                except StopIteration: True  #pronouns only set, no anchor is inferred, do nothing
        evaluation_entity_detection['fp']+=len(res_sets)
        evaluation_entity_detection_doc['fp']+=len(res_sets)

        
    #Document evaluation
    print 'Entity Detection: ',
    if key_sets==[]: entity_recall=1.
    else: entity_recall=float(evaluation_entity_detection_doc['tp'])/(evaluation_entity_detection_doc['tp']+evaluation_entity_detection_doc['fn'])
    if evaluation_entity_detection_doc['fp']==0: entity_precision=1.
    else: entity_precision=float(evaluation_entity_detection_doc['tp'])/(evaluation_entity_detection_doc['tp']+evaluation_entity_detection_doc['fp'])
    if entity_precision==0 and entity_recall==0: entity_f=0.
    else: entity_f= 2 * ((entity_recall*entity_precision)/(entity_recall+entity_precision))
    print 'R:', "%.2f" % (entity_recall*100),'%\t',
    print 'P:', "%.2f" % (entity_precision*100),'%\t',
    print 'F1:', "%.2f" % (entity_f*100),'%\t',
    print '(tp:',evaluation_entity_detection_doc['tp'],'| fn:',evaluation_entity_detection_doc['fn'],'| fp:',str(evaluation_entity_detection_doc['fp'])+')'

    print 'Entity Mentions:  ',
    if key_sets==[]: recall=precision=f1=1.
    else:
        if doc_tp+doc_fn==0: recall=0
        else:recall=float(doc_tp)/(doc_tp+doc_fn)
        if doc_tp+doc_fp==0: precision=0
        else:precision=float(doc_tp)/(doc_tp+doc_fp)
        if recall+precision==0: f1=0
        else:f1= 2* ((recall*precision)/(recall+precision))
    print 'R:', "%.2f" % (recall*100),'%\t',
    print 'P:', "%.2f" % (precision*100),'%\t',
    print 'F1:', "%.2f" % (f1*100),'%\t',
    print '(tp:',doc_tp,'| fn:',doc_fn,'| fp:',str(doc_fp)+')'
    print ''

#Evaluation over all documents
print '--------------------------------------------------------------------------\nTOTAL'

print 'Entity Detection: ',
if key_sets==[]: entity_recall=1.
else: entity_recall=float(evaluation_entity_detection['tp'])/(evaluation_entity_detection['tp']+evaluation_entity_detection['fn'])
if evaluation_entity_detection['fp']==0: entity_precision=1.
else: entity_precision=float(evaluation_entity_detection['tp'])/(evaluation_entity_detection['tp']+evaluation_entity_detection['fp'])
if entity_precision==0 and entity_recall==0: entity_f=0.
else: entity_f= 2 * ((entity_recall*entity_precision)/(entity_recall+entity_precision))
print 'R:', "%.2f" % (entity_recall*100),'%\t',
print 'P:', "%.2f" % (entity_precision*100),'%\t',
print 'F1:', "%.2f" % (entity_f*100),'%\t',
print '(tp:',evaluation_entity_detection['tp'],'| fn:',evaluation_entity_detection['fn'],'| fp:',str(evaluation_entity_detection['fp'])+')'

print 'Entity Mentions:  ',
if tp+fn==0: recall=0
else:recall=float(tp)/(tp+fn)
if tp+fp==0: precision=0
else:precision=float(tp)/(tp+fp)
if recall+precision==0: f1=0
else:f1= 2* ((recall*precision)/(recall+precision))
print 'R:', "%.2f" % (recall*100),'%\t',
print 'P:', "%.2f" % (precision*100),'%\t',
print 'F1:', "%.2f" % (f1*100),'%\t',
print '(tp:',tp,'| fn:',fn,'| fp:',str(fp)+')'

print 'F_harm:', "%.2f" % ((2 * (entity_f*f1)/(entity_f+f1))*100),'%'

print '--------------------------------------------------------------------------'
print 'Named Entity classes:\n'

if key_sets!=[]:
    sorted_ne_types=sorted([(evaluation_entity_detection_ne[ne_type]['tp']+evaluation_entity_detection_ne[ne_type]['fn'],ne_type) for ne_type in evaluation_entity_detection_ne.keys()],reverse=True)
    sorted_ne_types=[ne_type[1] for ne_type in sorted_ne_types]
    for k in sorted_ne_types:
        print k
        if evaluation_entity_detection_ne.has_key(k):
            print 'Entity Detection: ',
            if evaluation_entity_detection_ne[k]['tp']+evaluation_entity_detection_ne[k]['fn']==0: recall=0
            else:recall=float(evaluation_entity_detection_ne[k]['tp'])/(evaluation_entity_detection_ne[k]['tp']+evaluation_entity_detection_ne[k]['fn'])
            if evaluation_entity_detection_ne[k]['tp']+evaluation_entity_detection_ne[k]['fp']==0: precision=0
            else:precision=float(evaluation_entity_detection_ne[k]['tp'])/(evaluation_entity_detection_ne[k]['tp']+evaluation_entity_detection_ne[k]['fp'])
            if recall+precision==0: f1e=0
            else:f1e= 2* ((recall*precision)/(recall+precision))
            print 'R:', "%.2f" % (recall*100),'%\t',
            print 'P:', "%.2f" % (precision*100),'%\t',
            print 'F1:', "%.2f" % (f1e*100),'%\t',
            print '(tp:',evaluation_entity_detection_ne[k]['tp'],'| fn:',evaluation_entity_detection_ne[k]['fn'],'| fp:',str(evaluation_entity_detection_ne[k]['fp'])+')'
        if evaluation_ne.has_key(k):
            print 'Entity Mentions:  ',
            if evaluation_ne[k]['tp']+evaluation_ne[k]['fn']==0: recall=0
            else:recall=float(evaluation_ne[k]['tp'])/(evaluation_ne[k]['tp']+evaluation_ne[k]['fn'])
            if evaluation_ne[k]['tp']+evaluation_ne[k]['fp']==0: precision=0
            else:precision=float(evaluation_ne[k]['tp'])/(evaluation_ne[k]['tp']+evaluation_ne[k]['fp'])
            if recall+precision==0: f1=0
            else:f1= 2* ((recall*precision)/(recall+precision))
            print 'R:', "%.2f" % (recall*100),'%\t',
            print 'P:', "%.2f" % (precision*100),'%\t',
            print 'F1:', "%.2f" % (f1*100),'%\t',
            print '(tp:',evaluation_ne[k]['tp'],'| fn:',evaluation_ne[k]['fn'],'| fp:',str(evaluation_ne[k]['fp'])+')'
        if evaluation_ne.has_key(k) and evaluation_entity_detection_ne.has_key(k):
            print 'F_harm:', "%.2f" % ((2 * (f1e*f1)/(f1e+f1))*100),'%'
        print ''

