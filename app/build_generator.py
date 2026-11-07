import re
import xml.etree.ElementTree as ET


JUNIT_VERSION = "5.14.4"
MAVEN_COMPILER_VERSION = "3.16.0"
MAVEN_SUREFIRE_VERSION = "3.6.0"


def normalizar_artifact_id(nome):
    """
    Converte o nome do repositório em um
    artifactId Maven simples.
    """

    nome = nome.strip().lower()

    nome = re.sub(
        r"[^a-z0-9._-]+",
        "-",
        nome,
    )

    nome = nome.strip("-")

    if not nome:
        raise ValueError(
            "Não foi possível gerar artifactId."
        )

    return nome


def gerar_pom_maven(
    nome_completo,
    java_release,
):
    """
    Gera deterministicamente um pom.xml.

    A IA não participa da geração deste arquivo.
    """

    if java_release not in {
        "8",
        "11",
        "17",
        "21",
        "25",
        "26",
}:
        raise ValueError(
            "Versão Java não suportada."
        )

    try:
        proprietario, repositorio = (
            nome_completo.split("/", 1)
        )

    except ValueError as erro:
        raise ValueError(
            "Nome de repositório inválido."
        ) from erro

    artifact_id = normalizar_artifact_id(
        repositorio
    )

    proprietario = re.sub(
        r"[^a-zA-Z0-9_.-]",
        "",
        proprietario,
    ).lower()

    if not proprietario:
        raise ValueError(
            "Proprietário inválido."
        )

    group_id = (
        f"io.github.{proprietario}"
    )

    pom = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">

    <modelVersion>4.0.0</modelVersion>

    <groupId>{group_id}</groupId>
    <artifactId>{artifact_id}</artifactId>
    <version>1.0-SNAPSHOT</version>

    <properties>
        <maven.compiler.release>{java_release}</maven.compiler.release>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <junit.version>{JUNIT_VERSION}</junit.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>${{junit.version}}</version>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>{MAVEN_COMPILER_VERSION}</version>
            </plugin>

            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>{MAVEN_SUREFIRE_VERSION}</version>
            </plugin>
        </plugins>
    </build>

</project>
"""

    # Confirma que produzimos XML válido.
    try:
        ET.fromstring(pom)

    except ET.ParseError as erro:
        raise RuntimeError(
            "O pom.xml gerado é inválido."
        ) from erro

    return pom