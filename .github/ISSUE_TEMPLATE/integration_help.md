name: Integration Help
description: Get help integrating Memory Parasite into your agent
labels: ["help-wanted"]
body:
  - type: textarea
    id: description
    attributes:
      label: Agent Type
      description: What kind of agent are you building? (DEX, NFT, etc.)
    validations:
      required: true
  - type: textarea
    id: error
    attributes:
      label: Issues/Errors
      description: What specific issue are you facing during integration?
