// ПОВНА СИСТЕМА ЖІНОЧОГО ЗДОРОВ'Я
// Версія 3.0 - Інтегрована система з 3-бальною шкалою
// Включає: гормони, СПКЯ, кандидоз, ВПЛ, дієти, тренування
// Для AI асистента та веб-додатку PantelMed

const COMPLETE_WOMENS_HEALTH_SYSTEM = {
  // ===========================================
  // КОНФІГУРАЦІЯ ТА МЕТАДАНІ
  // ===========================================
  module_config: {
    name: 'complete_womens_health',
    version: '3.0',
    gender_restriction: 'female_only',
    requires_age: true,
    scoring_system: '3_point_scale', // 0-2 балів
    age_ranges: {
      reproductive: '18-45',
      perimenopause: '45-55', 
      postmenopause: '55+'
    },
    languages: ['uk', 'en'],
    default_language: 'uk'
  },

  // ===========================================
  // ОЦІНКА ЕСТРАДІОЛУ (3-бальна система)
  // ===========================================
  estradiol_assessment: {
    meta: {
      name: 'Естрадіол та естрогенний баланс',
      emoji: '🌸',
      title: '🌸 ЕСТРАДІОЛ - основний жіночий гормон',
      description: 'регулює менструальний цикл, настрій, кісткову щільність, серцево-судинну систему',
      dysfunction_effects: 'може призводити до ПМС, нерегулярного циклу, набряків, емоційних коливань',
      type: 'female_hormone',
      threshold: 3,
      priority: 'high'
    },

    questions: {
      primary: [
        {
          id: 'est_p1',
          text: 'Чи відчуваєте болючість або набряклість грудей перед місячними?',
          weight: 1.0,
          clinical_significance: 'high',
          type: 'multiple_choice',
          options: [
            { text: 'Так, дуже болюче', score: 2 },
            { text: 'Іноді, легкий дискомфорт', score: 1 },
            { text: 'Ні, ніколи', score: 0 }
          ]
        },
        {
          id: 'est_p2',
          text: 'Чи маєте надмірні виділення або кровомазання між циклами?',
          weight: 1.2,
          clinical_significance: 'high',
          type: 'multiple_choice',
          options: [
            { text: 'Так, часто', score: 2 },
            { text: 'Іноді', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        },
        {
          id: 'est_p3',
          text: 'Чи є набряки або затримка води в організмі перед менструацією?',
          weight: 1.0,
          clinical_significance: 'high',
          type: 'multiple_choice',
          options: [
            { text: 'Так, сильні набряки', score: 2 },
            { text: 'Легкі набряки', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        },
        {
          id: 'est_p4',
          text: 'Чи є надмірна дратівливість/емоційні гойдалки в другій фазі циклу?',
          weight: 1.1,
          clinical_significance: 'high',
          type: 'multiple_choice',
          options: [
            { text: 'Так, дуже виражені', score: 2 },
            { text: 'Помірні зміни настрою', score: 1 },
            { text: 'Ні, стабільний настрій', score: 0 }
          ]
        },
        {
          id: 'est_p5',
          text: 'Чи є прищі або жирна шкіра в певні фази циклу?',
          weight: 0.8,
          clinical_significance: 'medium',
          type: 'multiple_choice',
          options: [
            { text: 'Так, регулярно', score: 2 },
            { text: 'Іноді', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        },
        {
          id: 'est_p6',
          text: 'Чи відчуваєте сильну втому або апатію перед місячними?',
          weight: 1.0,
          clinical_significance: 'high',
          type: 'multiple_choice',
          options: [
            { text: 'Так, дуже сильну', score: 2 },
            { text: 'Помірну втому', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        },
        {
          id: 'est_p7',
          text: 'Чи маєте сильні менструальні болі, що потребують знеболювальних?',
          weight: 1.0,
          clinical_significance: 'high',
          type: 'multiple_choice',
          options: [
            { text: 'Так, дуже болючі', score: 2 },
            { text: 'Помірні болі', score: 1 },
            { text: 'Ні, безболісні', score: 0 }
          ]
        }
      ],

      additional: [
        {
          id: 'est_a1',
          text: 'Чи змінюється ваш апетит протягом циклу (особливо тяга до солодкого)?',
          trigger_condition: 'primary_score >= 4',
          weight: 0.8,
          type: 'multiple_choice',
          options: [
            { text: 'Так, дуже сильна тяга', score: 2 },
            { text: 'Так, помірна тяга', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        },
        {
          id: 'est_a2',
          text: 'Чи відчуваєте мігрені або головні болі пов\'язані з циклом?',
          trigger_condition: 'primary_score >= 4',
          weight: 0.9,
          type: 'multiple_choice',
          options: [
            { text: 'Так, сильні мігрені', score: 2 },
            { text: 'Так, помірні головні болі', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        }
      ]
    },

    interpretation: {
      severe_estrogen_dominance: {
        score_range: '10-14',
        description: 'Сильні ознаки естрогенового домінування',
        urgency: 'high',
        immediate_actions: [
          'Консультація гінеколога-ендокринолога протягом 1-2 тижнів',
          'Аналізи: естрадіол, прогестерон, пролактин, ТТГ',
          'УЗД органів малого тазу'
        ],
        supplements: [
          'DIM (індол-3-карбінол) 300-400 мг/день',
          'Кальцій D-глюкарат 1000-1500 мг/день',
          'Магній гліцинат 400-600 мг/день',
          'P-5-P (B6) 100-150 мг/день'
        ]
      },
      moderate_estrogen_dominance: {
        score_range: '6-9',
        description: 'Помірні ознаки естрогенового домінування',
        urgency: 'medium',
        supplements: [
          'DIM 200-300 мг/день',
          'Магній 300-400 мг/день',
          'P-5-P (B6) 50-100 мг/день'
        ]
      },
      mild_imbalance: {
        score_range: '3-5',
        description: 'Легкі ознаки гормональної дисрегуляції',
        urgency: 'low',
        supplements: [
          'Магній 300 мг/день',
          'Омега-3 1-2 г/день'
        ]
      },
      balanced: {
        score_range: '0-2',
        description: 'Нормальний естрогенний баланс',
        recommendations: ['Підтримка здорового способу життя']
      }
    }
  },

  // ===========================================
  // ОЦІНКА ПРОЛАКТИНУ (3-бальна система)
  // ===========================================
  prolactin_assessment: {
    meta: {
      name: 'Пролактин та репродуктивна функція',
      emoji: '🤱',
      title: '🤱 ПРОЛАКТИН - регулятор лактації та циклу',
      threshold: 2,
      priority: 'high'
    },

    questions: {
      primary: [
        {
          id: 'prl_p1',
          text: 'Чи спостерігаєте виділення з грудей поза лактацією?',
          weight: 2.0,
          type: 'multiple_choice',
          options: [
            { text: 'Так, регулярні виділення', score: 2 },
            { text: 'Іноді, незначні', score: 1 },
            { text: 'Ні, ніколи', score: 0 }
          ]
        },
        {
          id: 'prl_p2',
          text: 'Чи маєте низьке лібідо незалежно від фази циклу?',
          weight: 1.5,
          type: 'multiple_choice',
          options: [
            { text: 'Так, постійно низьке', score: 2 },
            { text: 'Іноді знижене', score: 1 },
            { text: 'Ні, нормальне', score: 0 }
          ]
        },
        {
          id: 'prl_p3',
          text: 'Чи порушений цикл: затримки, відсутність овуляції?',
          weight: 1.5,
          type: 'multiple_choice',
          options: [
            { text: 'Так, регулярні затримки', score: 2 },
            { text: 'Іноді нерегулярний', score: 1 },
            { text: 'Ні, регулярний цикл', score: 0 }
          ]
        },
        {
          id: 'prl_p4',
          text: 'Чи є головні болі або порушення зору?',
          weight: 2.0,
          note: 'може вказувати на мікроаденому гіпофіза',
          type: 'multiple_choice',
          options: [
            { text: 'Так, часті сильні головні болі', score: 2 },
            { text: 'Іноді головні болі', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        }
      ]
    },

    interpretation: {
      high_prolactin_urgent: {
        score_range: '6-10',
        description: 'Високий ризик гіперпролактинемії',
        urgency: 'urgent',
        immediate_actions: [
          'ТЕРМІНОВО до ендокринолога при виділеннях + головних болях',
          'Аналіз пролактину НАТЩЕ, В СПОКОЇ (повторити 2-3 рази)',
          'При пролактині >100 нг/мл - МРТ гіпофіза'
        ],
        supplements: [
          'P-5-P (активний B6) 100-200 мг/день',
          'Мака перуанська 2-3 г/день',
          'Вітекс (Chasteberry) 400-800 мг/день'
        ]
      },
      moderate_prolactin: {
        score_range: '3-5',
        description: 'Помірні ознаки підвищеного пролактину',
        urgency: 'medium',
        supplements: [
          'P-5-P (B6) 50-100 мг/день',
          'Магній 300-400 мг/день'
        ]
      },
      normal_prolactin: {
        score_range: '0-2',
        description: 'Нормальна функція пролактину'
      }
    }
  },

  // ===========================================
  // ОЦІНКА СПКЯ (3-бальна система)
  // ===========================================
  pcos_assessment: {
    meta: {
      name: 'СПКЯ - синдром полікістозних яєчників',
      emoji: '🥚',
      title: '🥚 СПКЯ - гормональний дисбаланс',
      threshold: 4,
      priority: 'high'
    },

    questions: {
      primary: [
        {
          id: 'pcos_p1',
          text: 'Чи нерегулярний ваш менструальний цикл?',
          weight: 2.5,
          type: 'multiple_choice',
          options: [
            { text: 'Цикли >35 днів або <8 циклів/рік', score: 2 },
            { text: 'Іноді затримки >1 тижня', score: 1 },
            { text: 'Регулярний цикл 24-35 днів', score: 0 }
          ]
        },
        {
          id: 'pcos_p2',
          text: 'Чи маєте надмірне оволосіння (гірсутизм)?',
          weight: 2.0,
          type: 'multiple_choice',
          options: [
            { text: 'Так, виражене на декількох ділянках', score: 2 },
            { text: 'Помірне (підборіддя, над губою)', score: 1 },
            { text: 'Ні, нормальне оволосіння', score: 0 }
          ]
        },
        {
          id: 'pcos_p3',
          text: 'Чи маєте акне на обличчі, спині або грудях у дорослому віці?',
          weight: 1.5,
          type: 'multiple_choice',
          options: [
            { text: 'Так, помірне постійне акне', score: 2 },
            { text: 'Легке акне або періодичне', score: 1 },
            { text: 'Ні, чиста шкіра', score: 0 }
          ]
        },
        {
          id: 'pcos_p4',
          text: 'Чи важко вам схуднути або легко набираєте вагу?',
          weight: 2.0,
          type: 'multiple_choice',
          options: [
            { text: 'Важко схуднути, легко набираю', score: 2 },
            { text: 'Іноді проблеми з вагою', score: 1 },
            { text: 'Нормальна вага, легко контролюю', score: 0 }
          ]
        },
        {
          id: 'pcos_p5',
          text: 'Чи є у вас ділянки темнішої, оксамитової шкіри?',
          weight: 1.5,
          note: 'acanthosis nigricans - ознака інсулінорезистентності',
          type: 'multiple_choice',
          options: [
            { text: 'Так, на шиї або пахвах', score: 2 },
            { text: 'Підозра на потемніння', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        },
        {
          id: 'pcos_p6',
          text: 'Чи маєте андрогенну алопецію (витоншення волосся)?',
          weight: 1.5,
          type: 'multiple_choice',
          options: [
            { text: 'Так, помітне поредіння', score: 2 },
            { text: 'Легке витоншення волосся', score: 1 },
            { text: 'Ні, нормальна щільність', score: 0 }
          ]
        },
        {
          id: 'pcos_p7',
          text: 'Чи маєте симптоми інсулінорезистентності?',
          weight: 2.0,
          type: 'multiple_choice',
          options: [
            { text: 'Так, сильна тяга до солодкого + втома після їжі', score: 2 },
            { text: 'Іноді тяга до вуглеводів', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        }
      ]
    },

    interpretation: {
      very_high_risk: {
        score_range: '10-16',
        description: 'Дуже високий ризик СПКЯ',
        urgency: 'urgent',
        probability: '>80%',
        immediate_actions: [
          'ТЕРМІНОВО до гінеколога-ендокринолога (протягом 1-2 тижнів)',
          'УЗД органів малого тазу (трансвагінальне)',
          'Повна гормональна панель'
        ],
        supplements: [
          'Інозитол (міо + D-хіро) 2-4 г/день в співвідношенні 40:1',
          'Берберин 500 мг 2-3 рази/день',
          'Омега-3 2-3 г/день',
          'Вітамін D3 + K2',
          'Магній 400-600 мг/день'
        ]
      },
      high_risk: {
        score_range: '6-9',
        description: 'Високий ризик СПКЯ',
        urgency: 'high',
        probability: '60-80%'
      },
      moderate_risk: {
        score_range: '3-5',
        description: 'Помірний ризик або окремі ознаки СПКЯ',
        urgency: 'medium',
        probability: '30-60%'
      },
      low_risk: {
        score_range: '0-2',
        description: 'Низький ризик СПКЯ',
        probability: '<30%'
      }
    }
  },

  // ===========================================
  // ОЦІНКА КАНДИДОЗУ (3-бальна система)
  // ===========================================
  candidiasis_assessment: {
    meta: {
      name: 'Оцінка молочниці',
      emoji: '🌱',
      description: 'Оцінка вульвовагінального кандидозу',
      threshold: 3
    },

    questions: {
      primary: [
        {
          id: 'cand_p1',
          text: 'Чи є свербіж або печіння в піхвовій зоні?',
          weight: 1.2,
          type: 'multiple_choice',
          options: [
            { text: 'Так, сильне', score: 2 },
            { text: 'Помірне', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        },
        {
          id: 'cand_p2',
          text: 'Чи є білі, густі виділення (як сир)?',
          weight: 1.2,
          type: 'multiple_choice',
          options: [
            { text: 'Так, виражені', score: 2 },
            { text: 'Помірні', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        },
        {
          id: 'cand_p3',
          text: 'Чи приймали антибіотики останні 3 місяці?',
          weight: 1.0,
          type: 'multiple_choice',
          options: [
            { text: 'Так, тривалий курс', score: 2 },
            { text: 'Так, короткий курс', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        },
        {
          id: 'cand_p4',
          text: 'Чи є підвищена тяга до солодкого?',
          weight: 1.0,
          type: 'multiple_choice',
          options: [
            { text: 'Так, часто їм солодке', score: 2 },
            { text: 'Іноді', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        }
      ]
    },

    recommendations: {
      high_risk: {
        score_range: '4-8',
        immediate_actions: [
          'Консультація гінеколога',
          'Аналіз виділень (мікроскопія, культура)'
        ],
        supplements: [
          'Пробіотики (Lactobacillus rhamnosus, L. reuteri) 10-20 млрд КУО/день',
          'NAC 600-1200 мг/день',
          'Омега-3 2 г/день'
        ],
        lifestyle: [
          'Обмеження цукру (<30 г/день)',
          'Носіння бавовняної білизни',
          'Йогурт із живими культурами'
        ]
      },
      low_risk: {
        score_range: '0-3',
        supplements: ['Пробіотики 10 млрд КУО/день'],
        lifestyle: ['Обмеження цукру', 'Бавовняна білизна']
      }
    }
  },

  // ===========================================
  // ОЦІНКА ВПЛ ТА ІМУНІТЕТУ (3-бальна система)
  // ===========================================
  hpv_assessment: {
    meta: {
      name: 'Оцінка ВПЛ та імунітету',
      emoji: '🛡️',
      description: 'Оцінка ризику ВПЛ, підтримка імунітету та профілактика',
      threshold: 3
    },

    questions: {
      primary: [
        {
          id: 'hpv_p1',
          text: 'Чи був позитивний тест на ВПЛ (HPV-ДНК)?',
          weight: 1.5,
          type: 'multiple_choice',
          options: [
            { text: 'Так, онкогенні типи (16/18)', score: 2 },
            { text: 'Так, низького ризику або невідомо', score: 1 },
            { text: 'Ні, негативний', score: 0 }
          ]
        },
        {
          id: 'hpv_p2',
          text: 'Чи є генітальні бородавки або зміни на шийці матки?',
          weight: 1.2,
          type: 'multiple_choice',
          options: [
            { text: 'Так, підтверджено', score: 2 },
            { text: 'Підозра', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        },
        {
          id: 'hpv_p3',
          text: 'Чи була вакцинація проти ВПЛ (Gardasil)?',
          weight: 1.0,
          type: 'multiple_choice',
          options: [
            { text: 'Ні, не вакцинована', score: 2 },
            { text: 'Так, частково', score: 1 },
            { text: 'Так, повний курс', score: 0 }
          ]
        },
        {
          id: 'hpv_p4',
          text: 'Чи є часті інфекції, свербіж або кандидоз?',
          weight: 1.0,
          type: 'multiple_choice',
          options: [
            { text: 'Так, часто', score: 2 },
            { text: 'Іноді', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        },
        {
          id: 'hpv_p5',
          text: 'Чи є дефіцит заліза (втома, випадіння волосся)?',
          weight: 0.9,
          type: 'multiple_choice',
          options: [
            { text: 'Так, підтверджено аналізами', score: 2 },
            { text: 'Підозрюю', score: 1 },
            { text: 'Ні', score: 0 }
          ]
        }
      ]
    },

    recommendations: {
      high_risk: {
        score_range: '5-10',
        immediate_actions: [
          'Консультація гінеколога-онколога',
          'HPV-ДНК тест і ПАП-тест щорічно',
          'Вакцинація Gardasil 9 (якщо вік <45 років)'
        ],
        supplements: [
          'NAC 600-1200 мг/день (натще, 1-3 місяці)',
          'Залізо хелат 25-50 мг/день + Вітамін C 500 мг (якщо ферритин <50)',
          'Вітамін D3 5000 МО/день (до рівня 40-60 нг/мл)',
          'Селен 200 мкг/день',
          'AHCC (екстракт шиїтаке) 1-3 г/день',
          'Пробіотики (L. rhamnosus, L. reuteri) 10-20 млрд КУО/день',
          'Кокосове масло 1-2 ст. л./день',
          'Олія орегано 200-400 мг/день (4-6 тижнів)'
        ],
        lifestyle: [
          'Антисептик для рук після контактів (70% спирт)',
          'Бавовняна білизна, уникнення вологих купальників',
          'Безпечний секс (кондоми)',
          'Уникнення куріння',
          'Сон 7-9 годин'
        ],
        diet: [
          'Протизапальна: ягоди, зелень, омега-3 (2-3 г/день)',
          'Обмеження цукру (<30 г/день), вуглеводів (<100 г/день)',
          'Йогурт із живими культурами'
        ]
      },
      low_risk: {
        score_range: '0-4',
        immediate_actions: ['ПАП-тест + HPV кожні 3 роки'],
        supplements: [
          'Вітамін D3 4000 МО/день',
          'Пробіотики 10 млрд КУО/день',
          'Кокосове масло 1 ст. л./день'
        ]
      }
    }
  },

  // ===========================================
  // СИСТЕМА ДІЄТ ТА ТРЕНУВАНЬ
  // ===========================================
  nutrition_training_system: {
    calculate_calories: function(userInfo) {
      const { weight, height, age, gender, activity_level } = userInfo;
      const bmr = gender === 'male' ?
        10 * weight + 6.25 * height - 5 * age + 5 :
        10 * weight + 6.25 * height - 5 * age - 161;
      const activity_multipliers = {
        sedentary: 1.2,
        light: 1.375,
        moderate: 1.55,
        active: 1.725,
        very_active: 1.9
      };
      return Math.round(bmr * (activity_multipliers[activity_level] || 1.55));
    },

    female_diets: {
      pcos: {
        macros: { protein: 0.3, carbs: 0.4, fats: 0.3 },
        recommendations: [
          'Низьковуглеводна дієта (<100 г/день)',
          'Продукти з низьким ГІ: броколі, шпинат, ягоди',
          'Білки: риба, курка, яйця',
          'Жири: авокадо, омега-3 (2-3 г/день)'
        ],
        supplements: [
          'Інозитол 2-4 г/день (міо:D-хіро = 40:1)',
          'Берберин 500 мг 2-3 рази/день',
          'NAC 600-1200 мг/день'
        ],
        lifestyle: [
          'Інтервальне голодування 16:8',
          'Кардіо + силові 3-5 разів/тиждень'
        ]
      },
      perimenopause: {
        macros: { protein: 0.35, carbs: 0.3, fats: 0.35 },
        recommendations: [
          'Протизапальна дієта: ягоди, жирна риба, куркума',
          'Обмеження кофеїну (<200 мг/день)',
          'Клітковина: 25-30 г/день'
        ],
        supplements: [
          'Чорний кмин 500-1000 мг/день',
          'Вітамін D3 5000 МО + K2 100 мкг/день',
          'Ашваганда 600 мг/день'
        ]
      },
      reproductive_cycle: {
        follicular_phase: {
          macros: { protein: 0.25, carbs: 0.5, fats: 0.25 },
          supplements: ['Вітамін E 400 МО/день', 'Фолієва кислота 800 мкг/день']
        },
        luteal_phase: {
          macros: { protein: 0.3, carbs: 0.35, fats: 0.35 },
          supplements: ['Магній 400-600 мг/день', 'P-5-P 50-100 мг/день']
        }
      }
    },

    training_protocols: {
      pcos: {
        program: [
          { 
            type: 'strength', 
            frequency: '3-4 рази/тиждень', 
            reps: '8-12', 
            intensity: '70-80% 1RM',
            exercises: ['Присідання', 'Станова тяга', 'Жим лежачи']
          },
          { 
            type: 'cardio', 
            frequency: '2 рази/тиждень', 
            duration: '20-30 хв', 
            intensity: 'HIIT (85% max HR)'
          }
        ]
      },
      perimenopause: {
        program: [
          {
            type: 'strength',
            frequency: '2-3 рази/тиждень',
            reps: '10-12',
            intensity: '60-75% 1RM'
          },
          {
            type: 'yoga_pilates',
            frequency: '2 рази/тиждень',
            duration: '30-45 хв'
          }
        ]
      }
    }
  },

  // ===========================================
  // ІНТЕГРАЦІЯ З МАГАЗИНОМ ТА КОНСУЛЬТАЦІЯМИ
  // ===========================================
  shop_integration: {
    supplements: [
      { 
        id: 'inositol', 
        name: 'Інозитол (міо + D-хіро 40:1)', 
        dose: '2-4 г/день', 
        price: 500, 
        category: ['pcos', 'female_health'] 
      },
      { 
        id: 'berberine', 
        name: 'Берберин', 
        dose: '500 мг 2-3 рази/день', 
        price: 400, 
        category: ['pcos', 'insulin'] 
      },
      { 
        id: 'nac', 
        name: 'NAC (N-ацетилцистеїн)', 
        dose: '600-1200 мг/день', 
        price: 300, 
        category: ['liver', 'immune', 'hpv'] 
      },
      { 
        id: 'vitamin_d_k2', 
        name: 'Вітамін D3 + K2', 
        dose: '5000 МО + 100 мкг/день', 
        price: 350, 
        category: ['female_health', 'bone_health', 'immune'] 
      },
      { 
        id: 'magnesium', 
        name: 'Магній гліцинат', 
        dose: '400-600 мг/день', 
        price: 250, 
        category: ['female_health', 'pms', 'sleep'] 
      },
      { 
        id: 'probiotics', 
        name: 'Пробіотики (L. rhamnosus + L. reuteri)', 
        dose: '10-20 млрд КУО/день', 
        price: 450, 
        category: ['candida', 'hpv', 'gut_health'] 
      },
      { 
        id: 'iron_chelate', 
        name: 'Залізо хелат + Вітамін C', 
        dose: '25-50 мг + 500 мг/день', 
        price: 280, 
        category: ['anemia', 'hpv', 'immune'] 
      },
      { 
        id: 'coconut_oil', 
        name: 'Кокосове масло органічне', 
        dose: '1-2 ст. л./день', 
        price: 200, 
        category: ['candida', 'hpv', 'antifungal'] 
      }
    ],

    telegram_bot: {
      endpoint: 'https://api.telegram.org/bot<TOKEN>/sendMessage',
      commands: [
        { command: '/order', action: 'create_order' },
        { command: '/recommend', action: 'get_supplement_recommendations' },
        { command: '/track', action: 'track_order' },
        { command: '/consult', action: 'book_consultation' }
      ]
    }
  },

  consultation_module: {
    ai_consultation: {
      recommendations: function(userResponses, testResults) {
        const recommendations = [];
        
        // Логіка на основі результатів опитування
        if (userResponses.pcos_total_score >= 6) {
          recommendations.push({
            type: 'supplement',
            item: 'Інозитол 2-4 г/день + консультація ендокринолога',
            urgency: 'high'
          });
        }
        
        if (userResponses.candida_total_score >= 4) {
          recommendations.push({
            type: 'supplement',
            item: 'Пробіотики 10-20 млрд КУО/день + обмеження цукру',
            urgency: 'medium'
          });
        }
        
        if (testResults && testResults.ferritin < 50) {
          recommendations.push({
            type: 'supplement',
            item: 'Залізо 25-50 мг/день + Вітамін C 500 мг/день',
            urgency: 'medium'
          });
        }
        
        return recommendations;
      }
    },

    personal_consultation: {
      booking: {
        telegram_form: 'https://t.me/PantelMedBot?start=consultation',
        required_data: ['userId', 'age', 'gender', 'main_concern', 'test_results']
      }
    }
  },

  // ===========================================
  // РОЗШИРЕНІ ЛАБОРАТОРНІ ПАНЕЛІ
  // ===========================================
  lab_panels: {
    female_hormone_panel: {
      timing: 'День 2-5 циклу або 19-23 день для прогестерону',
      tests: [
        'Естрадіол (E2)',
        'Прогестерон',
        'Пролактин',
        'ЛГ',
        'ФСГ',
        'ТТГ, Т4 вільний',
        'АМГ (антимюллеровий гормон)'
      ]
    },
    
    pcos_panel: {
      tests: [
        'Тестостерон загальний та вільний',
        'ДГЕА-С',
        '17-ОН-прогестерон',
        'ГСПГ',
        'Інсулін натще + HOMA-IR',
        'Глюкоза + HbA1c',
        'Ліпідограма'
      ]
    },
    
    immune_panel: {
      tests: [
        'Вітамін D (25-OH)',
        'Вітамін B12',
        'Фолієва кислота',
        'Залізо, феритин, трансферин',
        'Селен',
        'Цинк',
        'СРП (C-реактивний протеїн)'
      ]
    }
  },

  // ===========================================
  // API ФУНКЦІЇ
  // ===========================================
  api_functions: {
    // Комплексна оцінка всіх модулів
    assessCompleteHealth: function(responses, userProfile) {
      const assessments = {
        estrogen: this.parent.estradiol_assessment,
        prolactin: this.parent.prolactin_assessment,
        pcos: this.parent.pcos_assessment,
        candida: this.parent.candidiasis_assessment,
        hpv: this.parent.hpv_assessment
      };

      const results = {};
      const priorities = [];

      // Оцінка кожного модуля
      Object.keys(assessments).forEach(module => {
        const score = this.calculateModuleScore(responses, module);
        const interpretation = this.interpretScore(score, module);
        
        results[module] = {
          score: score,
          interpretation: interpretation,
          urgency: interpretation.urgency || 'low'
        };

        if (interpretation.urgency === 'urgent' || interpretation.urgency === 'high') {
          priorities.push({
            module: module,
            urgency: interpretation.urgency,
            description: interpretation.description
          });
        }
      });

      return {
        individual_assessments: results,
        priority_issues: priorities.sort((a, b) => 
          a.urgency === 'urgent' ? -1 : b.urgency === 'urgent' ? 1 : 0
        ),
        overall_health_score: this.calculateOverallScore(results),
        personalized_recommendations: this.generateRecommendations(results, userProfile)
      };
    },

    // Генерація персоналізованих рекомендацій
    generateRecommendations: function(results, userProfile) {
      const recommendations = {
        immediate_actions: [],
        supplements: [],
        lifestyle: [],
        diet: [],
        lab_tests: [],
        follow_up: []
      };

      // На основі результатів кожного модуля
      Object.keys(results).forEach(module => {
        if (results[module].urgency === 'urgent' || results[module].urgency === 'high') {
          const moduleRecommendations = this.getModuleRecommendations(module, results[module]);
          
          recommendations.immediate_actions.push(...(moduleRecommendations.immediate_actions || []));
          recommendations.supplements.push(...(moduleRecommendations.supplements || []));
          recommendations.lifestyle.push(...(moduleRecommendations.lifestyle || []));
          recommendations.diet.push(...(moduleRecommendations.diet || []));
        }
      });

      // Персоналізація на основі віку
      if (userProfile.age >= 45) {
        recommendations.supplements.push('Вітамін D3 5000 МО + K2 100 мкг/день');
        recommendations.lifestyle.push('Силові тренування 2-3 рази/тиждень для кісток');
      }

      // Видалення дублікатів
      Object.keys(recommendations).forEach(key => {
        recommendations[key] = [...new Set(recommendations[key])];
      });

      return recommendations;
    },

    // Розрахунок балів для модуля
    calculateModuleScore: function(responses, moduleName) {
      const moduleQuestions = this.getModuleQuestions(moduleName);
      let totalScore = 0;

      moduleQuestions.forEach(question => {
        const response = responses[question.id];
        if (response !== undefined) {
          totalScore += response * (question.weight || 1);
        }
      });

      return Math.round(totalScore);
    },

    // Отримання питань модуля
    getModuleQuestions: function(moduleName) {
      const moduleMapping = {
        estrogen: 'estradiol_assessment',
        prolactin: 'prolactin_assessment',
        pcos: 'pcos_assessment',
        candida: 'candidiasis_assessment',
        hpv: 'hpv_assessment'
      };
      
      const module = this.parent[moduleMapping[moduleName]];
      return [...module.questions.primary, ...(module.questions.additional || [])];
    },

    // Інтерпретація результатів
    interpretScore: function(score, moduleName) {
      const module = this.getModuleByName(moduleName);
      const interpretations = module.interpretation;
      
      for (const [key, interpretation] of Object.entries(interpretations)) {
        const range = interpretation.score_range.split('-').map(Number);
        if (score >= range[0] && score <= (range[1] || Infinity)) {
          return interpretation;
        }
      }
      
      return { description: 'Нормальний рівень', urgency: 'low' };
    },

    getModuleByName: function(moduleName) {
      const mapping = {
        estrogen: this.parent.estradiol_assessment,
        prolactin: this.parent.prolactin_assessment,
        pcos: this.parent.pcos_assessment,
        candida: this.parent.candidiasis_assessment,
        hpv: this.parent.hpv_assessment
      };
      return mapping[moduleName];
    },

    init: function(parent) {
      this.parent = parent;
      return this;
    }
  },

  // ===========================================
  // ІНІЦІАЛІЗАЦІЯ СИСТЕМИ
  // ===========================================
  init: function() {
    this.api_functions = this.api_functions.init(this);
    this.validateConfiguration();
    this.initializeCache();
    
    console.log('Complete Womens Health System v3.0 initialized successfully');
    console.log('✅ 3-point scoring system (0-2 points)');
    console.log('✅ Integrated modules: Estrogen, Prolactin, PCOS, Candida, HPV');
    console.log('✅ Nutrition & Training protocols');
    console.log('✅ Shop integration & Consultation module');
    
    return this;
  },

  validateConfiguration: function() {
    const requiredModules = [
      'estradiol_assessment',
      'prolactin_assessment', 
      'pcos_assessment',
      'candidiasis_assessment',
      'hpv_assessment',
      'nutrition_training_system',
      'shop_integration'
    ];
    
    const missingModules = requiredModules.filter(module => !this[module]);
    
    if (missingModules.length > 0) {
      console.warn('Missing required modules:', missingModules);
    } else {
      console.log('✅ All required modules validated successfully');
    }
  },

  initializeCache: function() {
    this._cache = {
      assessments: new Map(),
      recommendations: new Map(),
      labInterpretations: new Map(),
      nutritionPlans: new Map(),
      supplementRecommendations: new Map()
    };
  }
};

// Ініціалізація та експорт
const CompleteWomensHealthSystem = COMPLETE_WOMENS_HEALTH_SYSTEM.init();

export default CompleteWomensHealthSystem;
