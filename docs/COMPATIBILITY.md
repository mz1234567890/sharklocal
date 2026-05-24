# Compatibility

This table lists known vacuum models and their support for the REST and MQTT transports.
Visit a model's details page to see the full feature-level compatibility matrix for that model.

| Model        | REST | MQTT | Details                                |
| ------------ | :--: | :--: | -------------------------------------- |
| `RV2310CGUS` |  ❌  |  ✅  | [Details](compatibility/rv2310cgus.md) |
| `RV1001AEC`  |  ❌  |  ❌  | [Details](compatibility/rv1001aec.md)  |
| `UR2500SR`   |  ❌  |  ✅  | [Details](compatibility/ur2500sr.md)   |

> **Adding a new model?**
> The goal is to identify both supported and known unsupported models. This allows us to track and add new mappings targeted at specific models. Please open a PR with the following changes to contribute to this list.
>
> 1. Create `docs/compatibility/{model}.md` using the template in [`compatibility/template.md`](compatibility/template.md) as a reference.
> 2. Add a row to the table above with the model, transport support, and a link to the new file.
