from etk.etk import ETK
from etk.knowledge_graph import KGSchema, URI, BNode, Literal, Subject
from etk.extractors.glossary_extractor import GlossaryExtractor
from etk.etk_module import ETKModule


class ExampleETKModule(ETKModule):
    """
    Abstract class for extraction module
    """
    def __init__(self, etk):
        ETKModule.__init__(self, etk)
        self.name_extractor = GlossaryExtractor(self.etk.load_glossary("./names.txt"), "name_extractor",
                                                self.etk.default_tokenizer, case_sensitive=False, ngrams=1)

    def process_document(self, doc):
        """
        Add your code for processing the document
        """
        descriptions = doc.select_segments("projects[*].description")
        names = doc.select_segments("projects[*].name")
        projects = doc.select_segments("projects[*]")

        # Bind all your prefixes at here
        # None is default namespace
        doc.kg.bind(None, 'http://isi.edu/default-ns/')

        for p, n, d in zip(projects, names, descriptions):
            triple = Subject(URI(n.value))
            triple.add_property(URI("rdf:type"), URI("Software"))

            developers = doc.extract(self.name_extractor, d)
            p.store(developers, "members")
            for developer in developers:
                developer_t = Subject(BNode())
                developer_t.add_property(URI("rdf:type"), URI("Developer"))
                developer_t.add_property(URI("name"), Literal(developer.value))
                triple.add_property(URI("developer"), developer_t)
            doc.kg.add_subject(triple)

        return list()


if __name__ == "__main__":
    sample_input = {
        "projects": [
            {
                "name": "etk",
                "description": "version 2 of etk, implemented by Runqi Shao, Dongyu Li, Sylvia lin, Amandeep and "
                               "others."
            },
            {
                "name": "rltk",
                "description": "record linkage toolkit, implemented by Pedro, Mayank, Yixiang and several students."
            }
        ]
    }

    ontology = """
        @prefix : <http://example.org/> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        :Software a owl:Class ;
            rdfs:label "Software" .
        :Person a owl:Class ;
            rdfs:label "Person" .
        :Developer a owl:Class ;
            rdfs:label "Developer" .
        :name a owl:DatatypeProperty ;
            rdfs:domain :Person ;
            rdfs:range xsd:string .
        :developer a owl:ObjectProperty ;
            rdfs:label "developer" ;
            rdfs:domain :Software ;
            rdfs:range :Developer .
    """
    kg_schema = KGSchema()
    kg_schema.add_schema(ontology, 'ttl')
    etk = ETK(kg_schema=kg_schema, modules=ExampleETKModule)
    doc = etk.create_document(sample_input, doc_id="http://isi.edu/default-ns/projects")

    docs = etk.process_ems(doc)

    conforms, result_graph = docs[0].kg.validate()
    print(kg_schema.shacl.serialize('ttl'))
    if conforms:
        print(docs[0].kg.serialize('ttl'))
        print(docs[0].kg.serialize('nt'))
        print(docs[0].kg._resolve_uri.cache_info())
    else:
        print(result_graph.serialize('ttl'))
