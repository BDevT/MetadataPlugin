python -m venv ./venv
. venv/bin/activate

pip install -r requirements.txt 

python source-example - periodically create a bagit package

python gui-example.py - Host a scicat ingestor plugin

plugins/a/..... - plugin that Watches for a bagit package and creates a scicat dataset


http://www.plantuml.com/plantuml/uml/SyfFKj2rKt3CoKnELR1Io4ZDoSa70000

#class diagram

```plantuml

PluginBase <|-- Plugin
PluginBase  -- HostServices 

PluginBase *-- "many" Property

Plugin : widget()

HostServices : save_dataset()

Property : name
Property : value

PluginBase : properties
PluginBase : log(str)


```


#sequence diagram

```plantuml
Host -> HostServices : create
HostServices -> HostServices : start

HostServices -> HostServices : discover plugins
HostServices -> Plugin : loadPlugin

Plugin -> HostServices : register
Plugin -> Plugin : createProperties
group loop
Plugin -> Plugin : discovery


Plugin -> HostServices : upload_metadata

HostServices -> scicat : upload_dataset
HostServices <- scicat : dataset id
Plugin <- HostServices : dataset_id
end
HostServices -> HostServices : finish
HostServices -> Plugin : finish
```


