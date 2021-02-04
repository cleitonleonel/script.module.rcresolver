# rcresolver

* Infomations:
    * Faça download do arquivo zip e o instale no kodi normalmente ou o adicione ao
    seu add-on como uma dependência:
    ```xml
      <requires>
          <import addon="script.module.rcresolver" version="1.0.0"/>
      </requires>
    ```  

* Obs:
    * Apenas kodi rodando python3, também vale lembrar que
    durante os testes encontrei erros ao importar o módulo em outros addons,
    caso ocorra erros ao tentar importar este módulo sugiro descompactar os arquivos
    copiando a pasta rcresolver para dentro de seu addon ou a incluindo ao site-packages do python3 em execução.

* Usage:

```python
import rcresolver

url = "https://redecanais.cloud/os-novos-mutantes-dublado-2020-1080p_ffcf7b87c.html"
stream = rcresolver.resolve(url)
print(stream)

```

# Este módulo ajudou você?

Se esta lib permitir que você fique à vontade para fazer uma doação =), pode ser R $ 0,50 hahahaha. Para isso, basta ler o qrcode abaixo.

![QRCode Doação](https://github.com/cleitonleonel/pypix/blob/master/qrcode.png?raw=true)


# Autor

Cleiton Leonel Creton ==> cleiton.leonel@gmail.com

