import type { ExerciseGuide } from './types';

// Free Exercise DB (public domain): level and muscles as published;
// steps translated to Spanish and condensed from its instructions.
export const BACK_GUIDES: Record<string, ExerciseGuide> = {
  'Bent_Over_Barbell_Row': {
    level: 'beginner',
    primaryMuscles: ['middle back'],
    secondaryMuscles: ['biceps', 'lats', 'shoulders'],
    steps: [
      'Coge la barra con agarre prono, flexiona un poco las rodillas e inclina el torso desde la cadera, con la espalda recta, hasta casi paralelo al suelo.',
      'Mantén la cabeza arriba y deja que la barra cuelgue delante de ti con los brazos perpendiculares al suelo; es la posición inicial.',
      'Sin mover el torso, espira y lleva la barra hacia ti con los codos pegados al cuerpo; los antebrazos solo sujetan el peso.',
      'Arriba, aprieta la espalda un instante; inspira y baja la barra despacio a la posición inicial.',
    ],
  },
  'Seated_Cable_Rows': {
    level: 'beginner',
    primaryMuscles: ['middle back'],
    secondaryMuscles: ['biceps', 'lats', 'shoulders'],
    steps: [
      'Siéntate en la máquina de remo con polea baja, apoya los pies en la plataforma con las rodillas ligeramente flexionadas y coge las asas con agarre neutro.',
      'Con los brazos extendidos, échate atrás hasta que el torso forme 90° con las piernas, pecho fuera y espalda ligeramente arqueada; notarás el estiramiento en los dorsales.',
      'Sin mover el torso, espira y tira de las asas hacia el abdomen con los brazos pegados al cuerpo.',
      'Aprieta la espalda un segundo y vuelve despacio a la posición inicial mientras inspiras.',
    ],
  },
  'Dumbbell_Incline_Row': {
    level: 'beginner',
    primaryMuscles: ['middle back'],
    secondaryMuscles: ['biceps', 'forearms', 'lats', 'shoulders'],
    steps: [
      'Apóyate boca abajo sobre un banco inclinado con una mancuerna en cada mano, agarre neutro y los brazos extendidos; es la posición inicial.',
      'Junta las escápulas y flexiona los codos para remar las mancuernas hacia los costados.',
      'Haz una pausa arriba y vuelve despacio a la posición inicial.',
    ],
  },
  'Barbell_Deadlift': {
    level: 'intermediate',
    primaryMuscles: ['lower back'],
    secondaryMuscles: ['calves', 'forearms', 'glutes', 'hamstrings', 'lats', 'middle back', 'quadriceps', 'traps'],
    steps: [
      'Colócate delante de la barra cargada, flexiona las rodillas e inclínate hacia delante con la espalda lo más recta posible.',
      'Coge la barra con agarre prono a la anchura de los hombros; si te cuesta sujetarla, usa agarre mixto o correas.',
      'Inicia el levantamiento empujando con las piernas y endereza el torso a la vez mientras espiras.',
      'Arriba, saca pecho y junta las escápulas, como un soldado en posición de firmes.',
      'Baja flexionando las rodillas e inclinando el torso desde la cadera, con la espalda recta, hasta que los discos toquen el suelo.',
    ],
  },
  'One-Arm_Dumbbell_Row': {
    level: 'beginner',
    primaryMuscles: ['middle back'],
    secondaryMuscles: ['biceps', 'lats', 'shoulders'],
    steps: [
      'Apoya una rodilla y la mano del mismo lado en un banco plano e inclina el torso hasta que quede paralelo al suelo.',
      'Coge la mancuerna con la otra mano, palma hacia el torso, y mantén la zona lumbar recta; es la posición inicial.',
      'Espira y sube la mancuerna hacia el costado del pecho con el brazo pegado al cuerpo y sin mover el torso.',
      'Arriba, aprieta la espalda: tira con los dorsales, no con el brazo; el antebrazo solo sujeta la mancuerna.',
      'Inspira y baja la mancuerna despacio a la posición inicial; al terminar la serie, cambia de lado.',
    ],
  },
  'Good_Morning': {
    level: 'intermediate',
    primaryMuscles: ['hamstrings'],
    secondaryMuscles: ['abdominals', 'glutes', 'lower back'],
    steps: [
      'Saca la barra del rack a la altura de los hombros y apóyala sobre la parte trasera de los hombros, como en una sentadilla, no encima.',
      'Mantén la espalda firme, las escápulas juntas y las rodillas ligeramente flexionadas, y da un paso atrás.',
      'Flexiona desde la cadera llevándola hacia atrás e inclínate hasta casi paralelo al suelo, con la espalda arqueada y el cuello alineado.',
      'Extiende la cadera con glúteos e isquios para volver a la posición inicial.',
    ],
  },
  'Hyperextensions_Back_Extensions': {
    level: 'beginner',
    primaryMuscles: ['lower back'],
    secondaryMuscles: ['glutes', 'hamstrings'],
    steps: [
      'Túmbate boca abajo en el banco de hiperextensiones con los tobillos bien sujetos bajo los rodillos.',
      'Ajusta la almohadilla superior para que los muslos apoyen planos y puedas flexionar la cintura sin restricción.',
      'Con el cuerpo recto, cruza los brazos sobre el pecho o ponlos tras la cabeza; es la posición inicial. Puedes sujetar un disco para más resistencia.',
      'Inspira y baja el torso despacio desde la cintura, con la espalda plana, hasta notar el estiramiento en los isquios; no redondees la espalda.',
      'Sube despacio hasta la posición inicial sin pasar de la línea recta ni balancear el torso.',
    ],
  },
  'Wide-Grip_Lat_Pulldown': {
    level: 'beginner',
    primaryMuscles: ['lats'],
    secondaryMuscles: ['biceps', 'middle back', 'shoulders'],
    steps: [
      'Siéntate en la máquina, elige el peso y ajusta la almohadilla de las rodillas a tu altura para que el peso no te levante.',
      'Coge la barra con agarre prono y las manos más abiertas que la anchura de los hombros.',
      'Con los brazos extendidos, inclina el torso unos 30° hacia atrás, arquea un poco la zona lumbar y saca pecho; es la posición inicial.',
      'Espira y baja la barra hasta la parte alta del pecho llevando hombros y codos abajo y atrás; solo se mueven los brazos, el torso quieto.',
      'Aprieta las escápulas un segundo y, mientras inspiras, sube la barra despacio hasta extender los brazos y estirar los dorsales.',
    ],
  },
  'Leverage_Iso_Row': {
    level: 'beginner',
    primaryMuscles: ['lats'],
    secondaryMuscles: ['biceps', 'middle back'],
    steps: [
      'Elige el peso y ajusta el asiento para que las asas queden a la altura del pecho.',
      'Coge las asas con agarre neutro o prono y los brazos extendidos; es la posición inicial.',
      'Tira de las asas hacia el torso juntando las escápulas mientras flexionas los codos.',
      'Haz una pausa al final del recorrido y vuelve despacio a la posición inicial.',
      'Entre repeticiones, no dejes que el peso apoye del todo en los topes para mantener la tensión.',
    ],
  },
  'Pullups': {
    level: 'beginner',
    primaryMuscles: ['lats'],
    secondaryMuscles: ['biceps', 'middle back'],
    steps: [
      'Cuélgate de la barra con agarre prono; abre las manos más que los hombros para agarre ancho, a su anchura para agarre medio o más cerradas para estrecho.',
      'Con los brazos extendidos, inclina el torso unos 30° hacia atrás, arquea un poco la zona lumbar y saca pecho; es la posición inicial.',
      'Espira y sube hasta que la barra toque la parte alta del pecho llevando hombros y codos abajo y atrás.',
      'Arriba, aprieta la espalda un segundo; solo se mueven los brazos y los antebrazos solo sujetan la barra.',
      'Inspira y baja despacio hasta extender los brazos del todo y estirar los dorsales.',
    ],
  },
  'Straight-Arm_Dumbbell_Pullover': {
    level: 'intermediate',
    primaryMuscles: ['chest'],
    secondaryMuscles: ['lats', 'shoulders', 'triceps'],
    steps: [
      'Deja una mancuerna de pie sobre un banco plano y túmbate cruzado sobre él apoyando solo los hombros; cadera por debajo del banco, pies firmes y cabeza fuera.',
      'Coge la mancuerna con las dos manos por debajo de uno de los discos y sujétala sobre el pecho con los brazos extendidos; es la posición inicial.',
      'Comprueba que la mancuerna está bien fijada: con discos sueltos podría desmontarse y caerte en la cara.',
      'Con los brazos rectos, inspira y baja el peso despacio en arco por detrás de la cabeza hasta notar el estiramiento en el pecho.',
      'Espira y vuelve por el mismo arco a la posición inicial; aguanta un segundo arriba antes de repetir.',
    ],
  },
  'Rack_Pulls': {
    level: 'intermediate',
    primaryMuscles: ['lower back'],
    secondaryMuscles: ['forearms', 'glutes', 'hamstrings', 'traps'],
    steps: [
      'Coloca la barra sobre los seguros del rack a la altura deseada: justo bajo las rodillas, justo encima o a medio muslo.',
      'Ponte en posición de peso muerto: pies bajo la cadera, agarre a la anchura de los hombros, espalda arqueada y cadera atrás para activar los isquios.',
      'Como el peso suele ser alto, puedes usar agarre mixto, agarre de gancho o correas.',
      'Con la mirada al frente, extiende cadera y rodillas y tira del peso arriba y atrás hasta bloquear, llevando los hombros atrás al final.',
      'Devuelve la barra a los seguros y repite.',
    ],
  },
  'Straight-Arm_Pulldown': {
    level: 'beginner',
    primaryMuscles: ['lats'],
    secondaryMuscles: [],
    steps: [
      'Coge la barra ancha de la polea alta con agarre prono más abierto que los hombros y da un par de pasos atrás.',
      'Inclina el torso unos 30° desde la cintura con los brazos extendidos al frente y los codos apenas flexionados; si no quedan extendidos, retrocede un poco más.',
      'Activa los dorsales y, sin flexionar los brazos, baja la barra contrayéndolos hasta que las manos queden junto a los muslos mientras espiras.',
      'Con los brazos rectos, vuelve a la posición inicial mientras inspiras.',
    ],
  },
  'T-Bar_Row_with_Handle': {
    level: 'beginner',
    primaryMuscles: ['middle back'],
    secondaryMuscles: ['biceps', 'lats'],
    steps: [
      'Fija un extremo de la barra en un landmine o en una esquina y carga el peso en el otro extremo.',
      'Colócate sobre la barra, pasa el asa en V por debajo junto al tope de los discos y levántate con cadera y piernas.',
      'Abre los pies, lleva la cadera atrás y saca pecho con los brazos extendidos; es la posición inicial.',
      'Tira del peso hacia la parte alta del abdomen juntando las escápulas y flexionando los codos, sin tirones ni trampas.',
      'Tras una breve pausa, vuelve a la posición inicial.',
    ],
  },
  'Leverage_High_Row': {
    level: 'beginner',
    primaryMuscles: ['middle back'],
    secondaryMuscles: ['lats'],
    steps: [
      'Elige el peso y ajusta el asiento para que llegues justo a las asas por encima de ti; ajusta la almohadilla de las rodillas para que te sujete.',
      'Coge las asas con agarre prono; es la posición inicial.',
      'Tira de las asas hacia el torso juntando las escápulas mientras flexionas los codos.',
      'Haz una pausa al final del recorrido y vuelve despacio a la posición inicial.',
      'Entre repeticiones, no dejes que el peso apoye del todo en los topes para mantener la tensión.',
    ],
  },
};
