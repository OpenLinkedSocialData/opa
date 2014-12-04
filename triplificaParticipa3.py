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
g.namespace_manager.bind("schema", "http://schema.org/")
g.namespace_manager.bind("part", "http://participa.br/")    

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
def QC(mstr):
    return cc[CN.index(mstr)]

def QF(mstr):
    return fr[FRN.index(mstr)]
############## INÍCIO DA TRIPLIFICAÇÃO
### Rotina de triplificação dos perfis, artigos e comentários
G(U(part),rdf.type,opa.ParticipationPortal)
# adicionar mais info sobre o participa aqui (propósito, órgãos vinculados, etc)

for pp in profiles:
    ### tabela profiles
    ind=opa.Member+"#"+Q_("identifier")
    G(ind,rdf.type,opa.Member)
    G( ind,opa.name, L(Q("name")) )
    q=Q("type")
    if q=="Person":
        G(ind,rdf.type,opa.Participant)
        G( ind,opa.mbox,U("mailto:%s"%(Qu("email"),)) )
    elif q=="Community":
        G(ind,rdf.type,opa.Group)
    else:
        G(ind,rdf.type,opa.Organization)
    
    G(ind,opa.visibleProfile, L(Q("visible"),xsd.boolean) )
    G(ind,opa.publicProfile, L(Q("public_profile"),xsd.boolean))
    if Q("lat") and Q("lng"):
        lugar=r.BNode()
        G(lugar,rdf.type,opa.Point )
        G(ind, opa.based_near, lugar )
        G(lugar,opa.lat, L(Q("lat")))
        G(lugar,opa.long,L(Q("lng")))

    G(ind,opa.created,L(Q("created_at"),xsd.dateTime))
    G(ind,opa.modified,L(Q("updated_at"),xsd.dateTime))

    ### tabela artigos
    profile_id=Q("id")
    AA=[i for i in articles if i[AN.index("profile_id")]==profile_id]
    for aa in AA:
        if QA("published") and Q("public_profile"):
            ART = opa.Article+"#"+str(QA("id"))
            G(ART,rdf.type,opa.Article)
            G(ART,opa.publisher,ind)
            tipo=QA("type")
            G(ART,opa.atype,L(tipo))
            if sum([foo in tipo for foo in ["::","Article","Event","Blog"]]):
                name=QA("name")
                if name !="Blog":
                    G(ART,opa.title,r.Literal(name))
                if tipo=='CommunityTrackPlugin::Track':
                    G(ART,opa.atype,opa.ParticipationTrack)
                if tipo=='CommunityTrackPlugin::Step':
                    G(ART,opa.atype,opa.ParticipationStep)
                    pid=QA("parent_id")
                    aa2=[xx for xx in articles if xx[AN.index("id")]==pid][0]
                    pid=aa2[AN.index("profile_id")]  # o pid é o mesmo sempre!
                    pp2=[xx for xx in profiles if xx[PN.index("id")]==pid][0]
                    ART2 = opa.Article+"#"+str(aa2[AN.index("id")])
                    G(ART2,opa.hasStep,ART)
            body=QA("body")
            if (body!=None) and ( not body.startswith("--- ")):
                G(ART,opa.body,L(remove_tags(body)) )
            abst=QA("abstract")
            if abst:
                G( ART,opa.abstract,r.Literal(remove_tags(abst)) )
            G(ART,opa.created,L( QA("created_at"),xsd.dateTime))
            G(ART,opa.modified,L(QA("updated_at"),xsd.dateTime))
            G(ART,dc.issued,L(QA("published_at"),xsd.dateTime))

    ### tabela comentários
    CC=[i for i in comments if i[CN.index("author_id")]==profile_id]
    for cc in CC:
        COM=opa.Comment+"#"+str(QC("id"))
        G(COM,rdf.type,opa.Comment)
        G(COM,opa.creator,ind)
        if cc[CN.index("title")]:
            G(COM,opa.title,L(QC("title")))
        G(COM,opa.body,L(remove_tags(QC("body"))))
        G(COM,opa.created,L(QC("created_at"),xsd.dateTime))
        if QC("source_type")!="ActionTracker::Record":
            ART=QC("referrer")
            if ART:
                ART = opa.Article+"#"+str(QC("source_id")) # VERIFICAR
                G(ART,opa.hasReply,COM)

            rip=str(QC("reply_of_id"))
            if rip:
                turi=opa.Comment+"#"+rip
                G(turi , opa.hasReply , COM )

            G(COM,opa.ip,L(QC("ip_address")))

### tabela friendships
AM=[]
for fr in friendships:
    fid1=QF("person_id")
    fid2=QF("friend_id")
    am=set([fid1,fid2])
    if am not in AM:
        AM.append(am)
        ind1,ind2=[(opa.Member+"#"+Q_("identifier")) for pp in profiles if pp[0] in am]
        g.add((ind1,opa.knows,ind2))
        tfr=r.URIRef(opa.Friendship+"#"+("%s-%s"%tuple(am)))
        G(tfr,rdf.type,opa.Friendship)
        G(tfr,opa.member,ind1)
        G(tfr,opa.member,ind2)
        G(ind1,opa.created,L(QF("created_at"),xsd.dateTime))
f=open("participaTriplestore.rdf","wb")
f.write(g.serialize())
f.close()
f=open("participaTriplestore.ttl","wb")
f.write(g.serialize(format="turtle"))
f.close()
