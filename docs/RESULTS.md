# Results

All numbers are pass@1: the share of 8 samples per task, over 200 tasks, that pass every geometric check. Training tasks and eval tasks come from seed 7, and no eval task appears in training. Confidence intervals are bootstraps over tasks. Comparisons between runs are paired, since every run is scored on the same 200 tasks.

## The main run

[configs/nemotron4b.yaml](../configs/nemotron4b.yaml), 600 GRPO steps, one RTX 4090.

| Step | Trained relations (stack, next to) | Held-out relation (between) |
| --- | --- | --- |
| 0 (base) | 1.8% | 10.8% |
| 100 | 51.7% | 39.1% |
| 200 | 98.4% | 62.2% |
| 300 | 99.3% | 73.1% |
| 400 | 99.6% | **78.6%** |
| 500 | 99.9% | 74.8% |
| 600 | 99.8% | 76.4% |

- **Gain on the held-out relation:** +67.7 points at the best checkpoint (95% CI +64.7 to +70.8). The best step is picked on the same curve, so treat that as slightly optimistic; step 600 is 76.4%.
- **Against best-of-8:** the base model solves 54.5% of held-out tasks in at least one of 8 tries. The trained model's single try beats that.
- **Crashes:** 570 of the base model's 1,600 held-out scripts crash (wrong `bpy` attributes, wrong argument names, syntax). At step 600, 8 do.
- **What's still wrong:** 370 held-out scenes run but fail a check. 360 of them fail only one: the middle object is in the right place and the right size but at the wrong height, so it isn't resting on the ground. Cubes (175) and spheres (185) make this mistake about equally often.
- **Cost:** 3 h 31 min of training, median step 20.1 s, peak whole-card memory 22.4 GiB with the desktop running.

The [full report](../results/nemotron4b/report.md) has the curves with confidence bands, the error mix and the top-scoring samples.

## Against TRL

The same experiment was first run with Hugging Face TRL 1.16 and PEFT: the same tasks, seed, LoRA rank and alpha, target modules, learning rate and schedule, 4 × 8 rollouts per step, temperature, no KL term, 600 steps, and the same eval harness. That code isn't in this repo; its per-checkpoint numbers are in [results/trl_comparison.json](../results/trl_comparison.json).

| Step | Held-out, TRL | Held-out, NeMo RL |
| --- | --- | --- |
| 100 | 31.4% | 39.1% |
| 200 | 34.1% | 62.2% |
| 300 | 48.0% | 73.1% |
| 400 | 51.2% | 78.6% |
| 500 | 60.9% | 74.8% |
| 600 | 63.2% | 76.4% |

At step 600 NeMo RL is ahead by +13.1 points (95% CI +10.0 to +16.4); at step 400, by +27.3. On the trained relations both reach 99.8%. NeMo RL was also faster: 3 h 31 min against 3 h 56 min of training.

### Why? Four hypotheses

1. **LoRA initialisation.** PEFT draws the LoRA `A` matrix with Kaiming-uniform (a = √5); Megatron-Bridge uses Xavier-uniform, which is 2.44× larger here. Adam's step on `B` doesn't depend on `A`'s scale, so the update `ΔW = B·A` inherits it: about 2.4× the effective learning rate. Measured on the adapters, ‖ΔW‖ at step 50 was 0.39 for TRL and 0.95 for NeMo RL (2.46×), and the early gradient norm was 3.6× higher.
2. **TRL's importance-sampling correction.** TRL 1.16 corrects by default for the gap between vLLM's sampling probabilities and the trainer's own. Here that gap was 0.021 nats per token early on (NeMo RL's was about 0.007), so per-sequence weights ranged from 0.001 to 2.3 with a mean of 0.63, shrinking many updates. The NeMo RL run had the correction off.
3. **Fused q/k/v.** Megatron trains one adapter on the fused `linear_qkv`, where PEFT trains three. Only 4 of the model's layers are attention (21 are Mamba), and about three quarters of the update lands in Mamba `in_proj`, so this is the weakest candidate.
4. **Luck.** One seed per stack. The seed-8 runs below measure it.

### Run C: matching 1 and 2 made it worse

Run C was TRL with Xavier-uniform `A` and the correction off, everything else unchanged. The prediction, written down before it ran, was 72–80% held-out.

| Step | ‖ΔW‖, TRL | ‖ΔW‖, Run C | ‖ΔW‖, NeMo RL | Held-out, Run C |
| --- | --- | --- | --- | --- |
| 50 | 0.39 | 0.95 | 0.95 | |
| 100 | 0.62 | 1.35 | 1.32 | 29.9% |
| 200 | 0.88 | 1.69 | 1.76 | 34.1% |
| 300 | 1.01 | 1.82 | 1.87 | 39.1% |
| 400 | 1.05 | 1.91 | 1.94 | 45.7% |
| 500 | 1.07 | 2.00 | 2.00 | 39.1% |
| 600 | 1.08 | 2.05 | 2.02 | **50.8%** |

The change did what hypothesis 1 said it would: Run C's update size tracks NeMo RL's almost exactly, and it learned the trained relations faster than either run. Training reward saturated by about step 150, and from then on fewer than 5% of prompts still got varied rewards.

It did not generalise like NeMo RL. On the held-out relation it finished at 50.8%, 12.4 points *below* the original TRL run (95% CI −17.1 to −7.9). Up to step 200, its held-out curve is the same as TRL's, while NeMo RL was already at 62%.

So the larger effective learning rate explains NeMo RL's training speed but not its better generalisation. Turning off the importance-sampling correction may have hurt rather than helped: TRL's sampling mismatch is 3× NeMo RL's, and with the correction off it goes uncorrected. Run C changed both at once, so it can't separate them.

## What's running and what's next

- **Seed 8 for both stacks** ([configs/nemotron4b-seed8.yaml](../configs/nemotron4b-seed8.yaml) here, and its TRL twin). If either stack moves more than about 8 points between seeds, the comparison needs more seeds before it means anything.
- **Xavier init with the correction left on.** If that beats TRL's 63%, the correction helps TRL rather than hurting it.
- **The ground-contact mistake.** Almost all remaining held-out failures are the middle object's height. The heights the model writes don't follow one pattern yet, so the next step is reading them, not guessing a fix.
