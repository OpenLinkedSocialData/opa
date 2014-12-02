#!/usr/bin/python
#-*- coding: utf-8 -*-

######################
# no Ubuntu, rode com:
# $ sudo apt-get install postgresql
# $ sudo service postgresql start
# $ sudo pip install rdflib
# $ sudo pip install psychopg2 
# $ wget http://vocab.e.gov.br/2014/01/opa.owl

# arrume o login e a base de dados com o BD correto
# (este script considera que o servidor postgres roda local,
# o usuário se chama "r" e a base "newdb") e rode com:
# $ python triplificaParticipa.py
# aproveite o arquivo criado: "storeOpaPopulada.rdf"
# para levantar um endpoint SparQL.
# Ex:
# $ sudo pip install rdflodapp
# $ rdflodapp storeOpaPopulada.rdf

# Mais detalhes em:
# http://sourceforge.net/p/labmacambira/fimDoMundo/ci/master/tree/textos/SparQL/sparqlParticipa.pdf?format=raw
# http://sourceforge.net/p/labmacambira/fimDoMundo/ci/master/tree/textos/SparQL/triplificaDisponibiliza.pdf?format=raw

import psycopg2, rdflib as r, sys,urllib
import re
TAG_RE = re.compile(r'<[^>]+>')
def remove_tags(text):
    return TAG_RE.sub('', text)
#from xml.etree import ElementTree
#def remove_tags(text):
#    ''.join(ElementTree.fromstring(text).itertext())

###########
### Banco de dados do Participa.br
con = psycopg2.connect(database='newdb', user='r')
cur = con.cursor()

# dados das tabelas
cur.execute('SELECT * FROM users')
users = cur.fetchall()
cur.execute('SELECT * FROM profiles')
profiles = cur.fetchall()
cur.execute('SELECT * FROM articles')
articles = cur.fetchall()
cur.execute('SELECT * FROM comments')
comments = cur.fetchall()
cur.execute('SELECT * FROM friendships')
friendships= cur.fetchall()

# nome das colunas nas tabelas
cur.execute("select column_name from information_schema.columns where table_name='users';")
UN=cur.fetchall()
UN=[i[0] for i in UN[::-1]]
cur.execute("select column_name from information_schema.columns where table_name='profiles';")
PN=cur.fetchall()
PN=[i[0] for i in PN[::-1]]
cur.execute("select column_name from information_schema.columns where table_name='articles';")
AN=cur.fetchall()
AN=[i[0] for i in AN[::-1]]
cur.execute("select column_name from information_schema.columns where table_name='comments';")
CN=cur.fetchall()
CN=[i[0] for i in CN[::-1]]
cur.execute("select column_name from information_schema.columns where table_name='friendships';")
FRN=cur.fetchall()
FRN=[i[0] for i in FRN[::-1]]

###########
### Namespaces usados na triplificação
rdf = r.namespace.RDF
foaf = r.namespace.FOAF
xsd = r.namespace.XSD
opa = r.Namespace("http://purl.org/socialparticipation/opa/")
ops = r.Namespace("http://purl.org/socialparticipation/ops/")
wsg = r.Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
dc2 = r.Namespace("http://purl.org/dc/elements/1.1/")
dc = r.Namespace("http://purl.org/dc/terms/")
sioc = r.Namespace("http://rdfs.org/sioc/ns#")
tsioc = r.Namespace("http://rdfs.org/sioc/types#")
skos = r.Namespace("http://www.w3.org/2004/02/skos/core#")
schema = r.Namespace("http://schema.org/")
# para entidades do participa:
part = r.Namespace("http://participa.br/") 

# criação do grafo rdf e atribuição dos identificadores dos prefixos
g = r.Graph()
g.namespace_manager.bind("rdf", r.namespace.RDF)    
g.namespace_manager.bind("foaf", r.namespace.FOAF)    
g.namespace_manager.bind("xsd", r.namespace.XSD)    
g.namespace_manager.bind("opa", "http://purl.org/socialparticipation/opa/")    
g.namespace_manager.bind("ops", "http://purl.org/socialparticipation/ops/")    
g.namespace_manager.bind("wsg", "http://www.w3.org/2003/01/geo/wgs84_pos#")    
g.namespace_manager.bind("dc2", "http://purl.org/dc/elements/1.1/")    
g.namespace_manager.bind("dc", "http://purl.org/dc/terms/")    
g.namespace_manager.bind("sioc", "http://rdfs.org/sioc/ns#")    
g.namespace_manager.bind("tsioc", "http://rdfs.org/sioc/types#")    
#g.namespace_manager.bind("skos", "http://www.w3.org/2004/02/skos/core#")    
g.namespace_manager.bind("schema", "http://schema.org/")
g.namespace_manager.bind("part", "http://participa.br/")    
#g.load("./opa.owl")

##############
### Preparando para triplificação
# funções auxiliares para acesso aos dados
def Qu(termo):
    user_id=pp[PN.index("user_id")]
    val=[i for i in users if i[0]==user_id][0][UN.index(termo)]
    return val
def G(S,P,O):
    g.add((S,P,O))
def L(data, datatype_=None):
    if datatype_:
        return r.Literal(data, datatype=datatype_)
    else:
        return r.Literal(data)
U=r.URIRef
QQ=urllib.quote
def Q_(mstr):
    return QQ(pp[PN.index(mstr)])
def Q(mstr):
    return pp[PN.index(mstr)]
def QA(mstr):
    return aa[AN.index(mstr)]


############## INÍCIO DA TRIPLIFICAÇÃO
### Rotina de triplificação dos perfis, artigos e comentários
G(U(part),rdf.type,opa.ParticipationPortal)
# adicionar mais info sobre o participa aqui (propósito, órgãos vinculados, etc)

for pp in profiles:
    ### tabela profiles
    #ind=r.URIRef(part+"profile/"+urllib.quote(pp[PN.index("identifier")]))
    ind=opa.Member+"#"+Q_("identifier")
    G(ind,rdf.type,opa.Member)
    #g.add((U(part),dc.contributor,ind))
    #g.add((U(part),opa.member,ind))
    #g.add((ind,ops.hasRole,ops.Executer))
    #g.add((ind,foaf.name,r.Literal(pp[PN.index("name")])))
    #g.add((ind,opa.name,L(pp[PN.index("name")])))
    G( ind,opa.name, L(Q("name")) )
    q=Q("type")
    if q=="Person":
        G(ind,rdf.type,opa.Participant)
#        G(ind,rdf.type,ops.Participant)
#        G(ind,rdf.type,foaf.Person)
        G( ind,opa.mbox,U("mailto:%s"%(Qu("email"),)) )
#        G( ind,foaf.mbox,r.URIRef("mailto:%s"%(Qu("email"),)) )
    elif q=="Community":
        #g.add((ind,rdf.type,foaf.Group))
        G(ind,rdf.type,opa.Group)
    else:
        #g.add((ind,rdf.type,foaf.Organization)) 
        G(ind,rdf.type,opa.Organization)
    #is_visible= r.Literal(pp[PN.index("visible")],datatype=xsd.boolean)
    
    G(ind,opa.visibleProfile, L(Q("visible"),xsd.boolean) )
    #g.add((ind,opa.publicProfile,r.Literal(pp[PN.index("public_profile")],datatype=xsd.boolean)))
    G(ind,opa.publicProfile, L(Q("public_profile"),xsd.boolean))
    if Q("lat") and Q("lng"):
        lugar=r.BNode()
        # usando lat lon do WGS84
        # Por princípio, aqui também usa namespace interno, embora
        # eu ao menos estranhe

        #g.add((lugar,rdf.type,wsg.Point ))
        G(lugar,rdf.type,opa.Point )
        #g.add((ind, foaf.based_near, lugar ))
        G(ind, opa.based_near, lugar )
        #g.add((lugar,wsg.lat, r.Literal(pp[PN.index("lat")])))
        G(lugar,opa.lat, L(Q("lat")))
        #g.add((lugar,wsg.long,r.Literal(pp[PN.index("lng")])))
        G(lugar,opa.long,L(Q("lng")))

    # usando Dublin Core Terms
    #g.add((ind,dc.created,r.Literal(pp[PN.index("created_at")],datatype= xsd.dateTime)))
    G(ind,opa.created,L(Q("created_at"),xsd.dateTime))
    #g.add((ind,dc.modified,r.Literal(pp[PN.index("updated_at")],datatype=xsd.dateTime)))
    G(ind,opa.modified,L(Q("updated_at"),xsd.dateTime))

    ### tabela artigos
    profile_id=Q("id")
    AA=[i for i in articles if i[AN.index("profile_id")]==profile_id]
    #print "autor"
    for aa in AA:
        #if aa[AN.index("published")] and Q("public_profile"):
        print "artigo"
        if QA("published") and Q("public_profile"):
            #ART=r.URIRef(part+urllib.quote(pp[PN.index("identifier")])+"/"+urllib.quote(aa[AN.index("path")]));
            ART = opa.Article+"#"+QQ(QA("path"));
            G(ART,rdf.type,opa.Article)
            #g.add((ind,ops.performsParticipation,ART))
            G(ART,opa.publisher,ind)
            #g.add((ART,dc.creator,ind))
            tipo=QA("type")
            #G(ART,dc2.type,L(tipo))
            G(ART,opa.atype,L(tipo))
            print tipo
            if sum([foo in tipo for foo in ["::","Article","Event","Blog"]]):
                name=QA("name")
                if name !="Blog":
                    g.add((ART,dc2.title,r.Literal(name)))
                if tipo=='CommunityTrackPlugin::Track':
                    g.add((ART,dc.type,opa.ParticipationTrack))
                if tipo=='CommunityTrackPlugin::Step':
                    # renomeada ParticipationEvent para ParticipationStep
                    g.add((ART,dc.type,opa.ParticipationStep))
                    pid=aa[AN.index("parent_id")]
                    aa2=[xx for xx in articles if xx[AN.index("id")]==pid][0]
                    pid=aa2[AN.index("profile_id")]  # o pid é o mesmo sempre!
                    pp2=[xx for xx in profiles if xx[PN.index("id")]==pid][0]
                    ART2=r.URIRef(part+urllib.quote(pp2[PN.index("identifier")])+"/"+urllib.quote(aa2[AN.index("path")].decode("utf8")));
                    # renomeadas propriedades da opa
                    g.add((ART2,opa.hasStep,ART))
                    g.add((ART,opa.isStepOf,ART2))
            body=aa[AN.index("body")]
            if (body!=None) and ( not body.startswith("--- ")):
                g.add((ART,schema.articleBody,r.Literal(remove_tags(body)) ))
            abst=aa[AN.index("abstract")]
            if abst:
                g.add((ART,dc.abstract,r.Literal(remove_tags(abst)) ))
            g.add((ART,dc.created,r.Literal( aa[AN.index("created_at")],datatype=xsd.dateTime)))
            g.add((ART,dc.modified,r.Literal(aa[AN.index("updated_at")],datatype=xsd.dateTime)))
            g.add((ART,dc.issued,r.Literal(aa[AN.index("published_at")],datatype=xsd.dateTime)))

    ### tabela comentários
    CC=[i for i in comments if i[CN.index("author_id")]==profile_id]
    for cc in CC:
        COM=r.URIRef(part+"comment/%i"%(cc[CN.index("id")],))
        g.add((ind,ops.performsParticipation,COM))
        g.add((COM,dc.creator,ind))
        g.add((COM,dc2.type,r.Literal("Comment")))
        g.add((COM,dc.type,tsioc.Comment))
        if cc[CN.index("title")]:
            g.add((COM,dc.title,r.Literal(cc[CN.index("title")])))
        g.add((COM,schema.text,r.Literal(remove_tags(cc[CN.index("body")]))))
        g.add((COM,dc.created,r.Literal(cc[CN.index("created_at")],datatype=xsd.dateTime)))
        if cc[CN.index("source_type")]!="ActionTracker::Record":
            ART=cc[CN.index("referrer")]
            if ART:
                ART=ART.replace("http://psocial.secretariageral.gov.br","http://participa.br").replace("http://psocial.sg.gov.br","http://participa.br")
                g.add((r.URIRef(ART),sioc.has_reply,COM))

            rip=cc[CN.index("reply_of_id")]
            if rip:
                turi=part+"comment/%i"%(rip,)
                g.add((r.URIRef(turi) , sioc.has_reply, COM ))

            g.add((COM,sioc.ip_address,r.Literal(cc[CN.index("ip_address")])))

### tabela friendships
AM=[]    
for fr in friendships:
    fid1=fr[FRN.index("person_id")]
    fid2=fr[FRN.index("friend_id")]
    am=set([fid1,fid2])
    if am not in AM:
        AM.append(am)
        fid1_,fid2_=[pp[PN.index("identifier")] for pp in profiles if pp[0] in am]
        fid1_,fid2_=urllib.quote(fid1_),urllib.quote(fid2_)
        ind1=r.URIRef(part+"profile/%s"%(fid1_,))
        ind2=r.URIRef(part+"profile/%s"%(fid2_,))
        g.add((ind1,foaf.knows,ind2))
        g.add((ind2,foaf.knows,ind1))
        tfr=r.URIRef(part+"friendship/%s/%s"%(fid1_,fid2_))
        g.add((tfr,rdf.type,opa.Friendship))
        g.add((tfr,foaf.member,ind1))
        g.add((tfr,foaf.member,ind2))
        g.add((ind1,dc.created,r.Literal(fr[FRN.index("created_at")],datatype=xsd.dateTime)))
        tfr2=r.URIRef(part+"friendship/%s/%s"%(fid2_,fid1_))
        g.add((tfr,skos.exactMatch,tfr2))
f=open("storeOpaPopulada.rdf","wb")
f.write(g.serialize())
f.close()
f=open("storeOpaPopuladaTTL.rdf","wb")
f.write(g.serialize(format="turtle"))
f.close()
