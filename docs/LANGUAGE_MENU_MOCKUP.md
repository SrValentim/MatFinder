# Visual Representation of Language Menu

## Menu Structure

```
┌─────────────────────────────────────────────────────────┐
│ MatFinder Ver. 4.4                              [_][□][X]│
├─────────────────────────────────────────────────────────┤
│ Arquivo  Configuração  Ferramentas  Sobre              │
│          ▼                                               │
│     ┌────────────────────────────────┐                  │
│     │ Chave API Materials Project... │                  │
│     │ Configurar Proxy...            │                  │
│     │ Idioma                       ▶ │──┐               │
│     └────────────────────────────────┘  │               │
│                      ┌──────────────────┘               │
│                      │                                   │
│                      ▼                                   │
│              ┌───────────────┐                          │
│              │ ⦿ Português   │  ← Currently selected    │
│              │ ○ English     │                          │
│              │ ○ Deutsch     │                          │
│              └───────────────┘                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## In English (when English is selected):

```
┌─────────────────────────────────────────────────────────┐
│ MatFinder Ver. 4.4                              [_][□][X]│
├─────────────────────────────────────────────────────────┤
│ File  Settings  Tools  About                           │
│       ▼                                                  │
│     ┌────────────────────────────────┐                  │
│     │ Materials Project API Key...   │                  │
│     │ Configure Proxy...             │                  │
│     │ Language                     ▶ │──┐               │
│     └────────────────────────────────┘  │               │
│                      ┌──────────────────┘               │
│                      │                                   │
│                      ▼                                   │
│              ┌───────────────┐                          │
│              │ ○ Português   │                          │
│              │ ⦿ English     │  ← Currently selected    │
│              │ ○ Deutsch     │                          │
│              └───────────────┘                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## In German (when German is selected):

```
┌─────────────────────────────────────────────────────────┐
│ MatFinder Ver. 4.4                              [_][□][X]│
├─────────────────────────────────────────────────────────┤
│ Datei  Einstellungen  Werkzeuge  Über                  │
│        ▼                                                 │
│     ┌────────────────────────────────────┐              │
│     │ Materials Project API-Schlüssel... │              │
│     │ Proxy konfigurieren...             │              │
│     │ Sprache                          ▶ │──┐           │
│     └────────────────────────────────────┘  │           │
│                      ┌──────────────────────┘           │
│                      │                                   │
│                      ▼                                   │
│              ┌───────────────┐                          │
│              │ ○ Português   │                          │
│              │ ○ English     │                          │
│              │ ⦿ Deutsch     │  ← Currently selected    │
│              └───────────────┘                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Dialog When Changing Language

### In Portuguese:
```
┌─────────────────────────────────────────┐
│ Reiniciar Aplicação                 [X] │
├─────────────────────────────────────────┤
│                                         │
│ O idioma foi alterado para English.    │
│                                         │
│ É necessário reiniciar a aplicação     │
│ para aplicar as mudanças.              │
│                                         │
│ Deseja reiniciar agora?                │
│                                         │
│              ┌─────┐  ┌─────┐          │
│              │ Sim │  │ Não │          │
│              └─────┘  └─────┘          │
│                                         │
└─────────────────────────────────────────┘
```

### In English:
```
┌─────────────────────────────────────────┐
│ Restart Application                 [X] │
├─────────────────────────────────────────┤
│                                         │
│ The language has been changed to       │
│ Deutsch.                                │
│                                         │
│ A restart is required to apply the     │
│ changes.                                │
│                                         │
│ Would you like to restart now?         │
│                                         │
│              ┌─────┐  ┌────┐           │
│              │ Yes │  │ No │           │
│              └─────┘  └────┘           │
│                                         │
└─────────────────────────────────────────┘
```

### In German:
```
┌─────────────────────────────────────────┐
│ Anwendung neu starten               [X] │
├─────────────────────────────────────────┤
│                                         │
│ Die Sprache wurde auf Português        │
│ geändert.                               │
│                                         │
│ Ein Neustart ist erforderlich, um die  │
│ Änderungen anzuwenden.                  │
│                                         │
│ Möchten Sie jetzt neu starten?         │
│                                         │
│              ┌─────┐  ┌──────┐         │
│              │ Ja  │  │ Nein │         │
│              └─────┘  └──────┘         │
│                                         │
└─────────────────────────────────────────┘
```

## Legend
- ⦿ = Selected radio button
- ○ = Unselected radio button  
- ▼ = Expanded menu
- ▶ = Submenu indicator
- [X] = Close button
