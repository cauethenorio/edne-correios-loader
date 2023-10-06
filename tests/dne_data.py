from operator import itemgetter

from edne_correios_loader.tables import SituacaoLocalidadeEnum, TipoLocalidadeEnum


def generate_localidade(faker):
    return (
        faker.unique.pyint(min_value=1000, max_value=100000),
        faker.estado_sigla(),
        faker.unique.city(),
        faker.unique.postcode(formatted=False),
        faker.enum(SituacaoLocalidadeEnum),
        faker.enum(TipoLocalidadeEnum),
        None,
        faker.unique.city(),
        faker.unique.pyint(min_value=100000, max_value=1000000),
    )


# bairros


def generate_bairro(faker, localidades):
    return (
        faker.unique.pyint(min_value=1000, max_value=100000),
        faker.estado_sigla(),
        faker.random.choice(localidades)[0],
        faker.unique.bairro(),
        faker.unique.bairro()[:5],
    )


# logradouros


def generate_logradouro(faker, localidades, bairros):
    return (
        faker.unique.pyint(min_value=1000, max_value=100000),
        faker.estado_sigla(),
        faker.random.choice(localidades)[0],
        faker.random.choice(bairros)[0],
        faker.random.choice([None, faker.random.choice(bairros)[0]]),
        faker.unique.street_name(),
        faker.random.choice([None, faker.street_suffix()]),
        faker.unique.postcode(formatted=False),
        faker.street_prefix(),
        faker.random.choice(["S", "N"]),
        faker.unique.street_name()[:5],
    )


def create_sorted_rows(fn, nrows):
    return sorted([fn() for _ in range(nrows)], key=itemgetter(0))
