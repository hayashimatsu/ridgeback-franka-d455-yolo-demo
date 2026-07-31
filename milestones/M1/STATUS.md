# M1 Status — Factory Scene and Object Catalog

- Owner: Agent 1
- State: `complete`
- Entry gate: `pass`; M0 clean-reopen baseline check passed at commit
  `5ac9552f273ca018feef9adaf8b7e1cda6cc1dcb`.
- Objective result: `pass`. The accepted factory scene is
  `scenes/ridgeback_franka_d455_yolo_demo_m1_r3.usd`; the protected baseline
  and user-reviewed source candidate remain unchanged.
- Step1 result: `pass`; 30 project-authored identities cover five fixed classes
  with three train, two validation, and one held-out identity per class.
- Step2 result: `pass`; the scene contains 20 semantic display objects, four per
  class, a hidden 30-asset library, and zero factory rigid bodies.
- Step3 correction result: `pass`; the left D455 camera uses the asset transform,
  the Panda clean pose is authored against the reviewed IKTarget, the public
  workflow captures a complete three-tier rack, and a second runtime target pose
  moves the hand and rigidly attached camera together.
- Protected baseline SHA-256:
  `a724cd7da8c31ced82cba32a41c4abdf75d8011e4baebf274079c30e2c44a7cc`.
- User-reviewed source candidate SHA-256:
  `05329ddde64616b1bc05287520002e3c862942572225006232bfa76ee0b01758`.
- Accepted M1 scene SHA-256:
  `092f9d445a9580946621601e4f918799e1959b9ad80302e1cbb9df67adfd6106`.
- Factory content SHA-256:
  `4cb30f7854f486bd77f83b5bd47530ce2d920f006d82bcbb82f3047b69a5ff49`.
- Acceptance: `validation/m1/acceptance.json`; representative left RGB and
  depth are under `validation/m1/golden/`.
- Runtime result: public `demo_start.py` ready, one IK subscription, zero
  controller errors, target startup translation `0.684 mm`, stereo baseline
  `0.095000 m`, 236,907 valid left-depth pixels, capture hash unchanged,
  callback count zero after stop, and final timeline stopped.
- Known limitations: proxy assets remain non-redistributable until repository
  license terms are supplied; joint4 is near its lower limit; Isaac Kit reports
  root dirty after reopen/render initialization, but no USD save occurred.
- M1 acceptance commit:
  `870eea1f07a43c7cbdd1f996989516fe8c917e81`.
- Push: `origin/main` contains the M1 acceptance commit and handoff commit
  `4ae3dac331b529442d2fdf291a18daece83ec6ff`.
- Next action: discuss M2 scope with the user before authoring or executing an
  M2 task. M2 has not started.
