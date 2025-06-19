import streamlit as st
import re
import io
import time
# Z3 kutubxonasi
from z3 import * # Z3 solverining barcha funksiyalarini import qilish

# Streamlit ilovasi uchun sahifa konfiguratsiyasi va uslublar
st.set_page_config(layout="centered", page_title="Mantiqiy Tenglamalar Yechimi (Z3)")
st.markdown(
    """
    <style>
    /* Asosiy sarlavha uslubi */
    .main-header {
        font-size: 3em;
        color: #4CAF50; /* Yashil rang */
        text-align: center;
        margin-bottom: 20px;
        font-family: 'Inter', sans-serif; /* Inter shrifti */
    }
    /* Kichik sarlavha uslubi */
    .sub-header {
        font-size: 1.8em;
        color: #555;
        margin-top: 25px;
        margin-bottom: 15px;
        border-bottom: 2px solid #eee;
        padding-bottom: 5px;
        font-family: 'Inter', sans-serif;
    }
    /* Tugma uslubi */
    .stButton>button {
        background-color: #4CAF50; /* Yashil rang */
        color: white;
        border-radius: 8px; /* Yumaloq burchaklar */
        padding: 10px 20px;
        font-size: 1.1em;
        border: none;
        cursor: pointer;
        transition: all 0.3s ease; /* Silliq animatsiya */
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); /* Soya */
    }
    .stButton>button:hover {
        background-color: #45a049; /* To'q yashil rang */
        transform: translateY(-2px); /* Tepaga siljish effekti */
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15); /* Kattaroq soya */
    }
    /* Matn kiritish maydonlari uslubi */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 1px solid #ddd;
        padding: 8px 12px;
        font-size: 1em;
    }
    /* Raqam kiritish maydonlari uslubi */
    .stNumberInput>div>div>input {
        border-radius: 8px;
        border: 1px solid #ddd;
        padding: 8px 12px;
        font-size: 1em;
    }
    /* Jadvallar uslubi (DataFrame) */
    .stTable, .stDataFrame {
        border-radius: 8px;
        overflow: hidden; /* Kontent tashqariga chiqmasligi uchun */
        margin-top: 20px;
        border: 1px solid #ddd;
    }
    /* Jadval sarlavhasi uslubi */
    .solution-table th {
        background-color: #f2f2f2 !important;
        color: #333 !important;
        font-weight: bold !important;
        padding: 10px !important;
        border-bottom: 2px solid #ddd !important;
    }
    /* Jadval katakchalari uslubi */
    .solution-table td {
        padding: 8px !important;
        border-bottom: 1px solid #eee !important;
    }
    /* Markdown orqali qo'shilgan h3 sarlavhalar */
    .stMarkdown h3 {
        color: #333;
        font-family: 'Inter', sans-serif;
    }
    /* Izoh qutisi uslubi */
    .note-box {
        background-color: #e6f7ff; /* Och ko'k fon */
        border-left: 5px solid #2196F3; /* Chap tomonda ko'k chegara */
        padding: 15px;
        margin-bottom: 20px;
        border-radius: 4px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

class LogSystems:
    '''
    Mantiqiy tenglamalar yoki mantiqiy tenglamalar tizimini Z3 solver yordamida yechuvchi klass.
    Ajoyib interfeys bilan Streamlit orqali ishlaydi.
    '''
    def __init__(self, x_count, y_count, var_names, equations_str, is_set=True):
        self.solutions_count = 0  # Tenglama (tizim) yechimlari soni
        self.z3_vars = {}         # O'zgaruvchi nomlarini (str) Z3 Boolean o'zgaruvchilariga bog'lash
        self.vars = var_names     # Funkciyadagi o'zgaruvchilar (str ro'yxati)
        self.display_names = []   # Foydalanuvchi kiritgan mos nomlar
        self.is_set = is_set      # O'zgaruvchilar to'plamlarini chiqarish kerakmi
        self.x_count = x_count    # x o'zgaruvchilari soni
        self.y_count = y_count    # y o'zgaruvchilari soni
        self.equations_str = equations_str # Tenglamalar matn ko'rinishida
        self.raw_equations = []   # Foydalanuvchi kiritgan dastlabki tenglamalar
        self.prepared_solutions = [] # Yechimlar (0/1 formatida, Z3 modelidan olingan)

        self._initialize_z3_vars()

    def _initialize_z3_vars(self):
        """O'zgaruvchi nomlari uchun Z3 Boolean o'zgaruvchilarini yaratadi."""
        for var_name in self.vars:
            self.z3_vars[var_name] = Bool(var_name)

    def _get_z3_expr(self, part_str, defined_vars_set):
        """Berilgan qism uchun Z3 ifodasini qaytaradi (o'zgaruvchi yoki inkorlangan o'zgaruvchi)."""
        is_negated = False
        var_name = part_str
        if part_str.startswith('!'):
            is_negated = True
            var_name = part_str[1:]
        
        if not re.fullmatch(r'[a-zA-Z]+[0-9]*', var_name) or var_name not in defined_vars_set:
            raise ValueError(f"Noma'lum yoki noto'g'ri o'zgaruvchi: '{part_str}'.")
        
        z3_var = self.z3_vars[var_name]
        return Not(z3_var) if is_negated else z3_var

    def prepare_assertions(self):
        '''
        Foydalanuvchi kiritgan tenglamalarni Z3 assertions (shartlar) formatiga tayyorlaydi.
        '''
        if not self.vars:
            raise ValueError("O'zgaruvchilar ro'yxati bo'sh. Iltimos, o'zgaruvchilarni kiriting.")
        
        assertions = [] # Z3 ga qo'shiladigan shartlar ro'yxati

        # Kiritilgan tenglamalarni satrlar ro'yxatiga ajratish
        self.raw_equations = [eq.strip() for eq in self.equations_str.split('\n') if eq.strip()]
        
        if not self.raw_equations:
            raise ValueError("Tenglamalar kiritilmagan. Iltimos, kamida bitta tenglama kiriting.")

        defined_vars_set = set(self.vars) # Barcha aniqlangan o'zgaruvchilar to'plami
        for eq_str in self.raw_equations:
            core_expr = eq_str.strip()
            # Tenglama "(IFODA) = 1" shaklida bo'lsa, ichki qismni olamiz
            if core_expr.startswith('(') and core_expr.endswith(') = 1'):
                core_expr = core_expr[1:-4].strip() # Example: `(x1 - (y1 + y3 + y5))`
            elif core_expr.endswith('= 1'): # Handle cases like 'x1 = 1' or '!x1 = 1'
                core_expr = core_expr[:-3].strip() # Example: `x1` or `!x1`
            
            try:
                assertion = self._parse_to_z3_expr(core_expr, defined_vars_set, eq_str)
                assertions.append(assertion)
            except ValueError as ve:
                raise ValueError(f"Tenglama '{eq_str}'ni tahlil qilishda xato: {ve}. Tenglama formatini tekshiring.")
            except Exception as e:
                raise Exception(f"Tenglama '{eq_str}'ni tahlil qilishda kutilmagan xato: {e}. Formatni tekshiring.")
        return assertions

    def _parse_to_z3_expr(self, expr_str, defined_vars_set, original_eq_str):
        """
        Mantiqiy ifoda qatorini tahlil qiladi va unga mos Z3 Boolean ifodasini qaytaradi.
        """
        expr_str = re.sub(r'\s+', '', expr_str) # Barcha bo'shliq belgilarini olib tashlash

        # 1. Implikatsiya: X - (Y1 + Y2 + ...)  -> Implies(X, Or(Y1, Y2, ...))
        match_implication = re.match(r'^(?P<antecedent_var>[a-zA-Z]+[0-9]*)-(?P<consequent_raw>\(.+\))$', expr_str)
        if match_implication:
            antecedent_var = match_implication.group('antecedent_var')
            consequent_raw = match_implication.group('consequent_raw')
            
            consequent_inner_str = consequent_raw.strip('()')
            consequent_parts = [p.strip() for p in consequent_inner_str.split('+')]
            
            consequent_z3_exprs = []
            for part in consequent_parts:
                consequent_z3_exprs.append(self._get_z3_expr(part, defined_vars_set))

            antecedent_z3_expr = self._get_z3_expr(antecedent_var, defined_vars_set)
            return Implies(antecedent_z3_expr, Or(consequent_z3_exprs))

        # 2. Ekvivalentlik (AND): (X1 * X2 * ...) = Y  -> And(X1, X2, ...) == Y
        match_equivalence_and = re.match(r'^\((?P<left_and_raw>[a-zA-Z0-9*!]+)\)=(?P<right_var>[a-zA-Z]+[0-9]*)$', expr_str)
        if match_equivalence_and:
            left_and_raw = match_equivalence_and.group('left_and_raw')
            right_var = match_equivalence_and.group('right_var')

            left_and_parts = [v.strip() for v in left_and_raw.split('*')]
            
            left_and_z3_exprs = []
            for part in left_and_parts:
                left_and_z3_exprs.append(self._get_z3_expr(part, defined_vars_set))
            
            right_z3_expr = self._get_z3_expr(right_var, defined_vars_set)
            return And(left_and_z3_exprs) == right_z3_expr

        # 3. Oddiy Inkor: !var -> Not(var)
        match_negation = re.match(r'^!(?P<var>[a-zA-Z]+[0-9]*)$', expr_str)
        if match_negation:
            var_name = match_negation.group('var')
            return self._get_z3_expr(var_name, defined_vars_set, negate=True) # Z3 Not funksiyasini ishlatish

        # 4. Oddiy Dizyunksiya (OR): var1+var2+... -> Or(var1, var2, ...)
        if '+' in expr_str:
            parts = expr_str.split('+')
            or_z3_exprs = []
            for part in parts:
                or_z3_exprs.append(self._get_z3_expr(part, defined_vars_set))
            return Or(or_z3_exprs)

        # 5. Oddiy Konyunksiya (AND): var1*var2*... -> And(var1, var2, ...)
        if '*' in expr_str:
            parts = expr_str.split('*')
            and_z3_exprs = []
            for part in parts:
                and_z3_exprs.append(self._get_z3_expr(part, defined_vars_set))
            return And(and_z3_exprs)
        
        # 6. Oddiy tenglik: var1 = var2 -> var1 == var2
        match_simple_eq = re.match(r'^(?P<var1>[a-zA-Z]+[0-9]*)=(?P<var2>[a-zA-Z]+[0-9]*)$', expr_str)
        if match_simple_eq:
            var1 = match_simple_eq.group('var1')
            var2 = match_simple_eq.group('var2')
            return self._get_z3_expr(var1, defined_vars_set) == self._get_z3_expr(var2, defined_vars_set)

        # 7. Oddiy o'zgaruvchi (u rost bo'lishi kerak): var -> var
        if re.fullmatch(r'[a-zA-Z]+[0-9]*', expr_str) and expr_str in defined_vars_set:
            return self._get_z3_expr(expr_str, defined_vars_set)

        raise ValueError(f"Tenglama formati noto'g'ri yoki qo'llab-quvvatlanmaydi: '{original_eq_str}'. Iltimos, yordam bo'limini tekshiring.")

    def solve(self):
        '''
        Z3 solver yordamida barcha mumkin bo'lgan yechimlarni topadi.
        '''
        self.solutions_count = 0
        self.prepared_solutions = []

        try:
            assertions = self.prepare_assertions() # Z3 assertions (shartlar) tayyorlash
        except ValueError as e:
            st.error(f"Tenglama yoki o'zgaruvchi xatosi: {e}")
            return None
        except Exception as e:
            st.error(f"Formulani tayyorlashda kutilmagan xato: {e}")
            return None

        # Z3 solverini ishga tushirish
        s = Solver()
        for assertion in assertions:
            s.add(assertion)

        # Barcha yechimlarni topish
        # Z3 barcha yechimlarni to'g'ridan-to'g'ri enumerate qilmaydi.
        # Har bir topilgan modelni qanoatlantirmaslik (block) orqali keyingi modelni qidiramiz.
        try:
            while s.check() == sat: # sat (satisfiable) - yechim mavjud
                model = s.model()
                current_solution = [0] * len(self.vars)
                for var_name_str in self.vars:
                    z3_bool_var = self.z3_vars[var_name_str]
                    # Agar modelda o'zgaruvchi mavjud bo'lsa va u True bo'lsa, 1 ni qo'ying
                    # Agar False bo'lsa, 0 ni qo'ying (default qiymat 0)
                    if model.evaluate(z3_bool_var) == True:
                        current_solution[self.vars.index(var_name_str)] = 1
                
                self.prepared_solutions.append(current_solution)
                self.solutions_count += 1
                
                # Topilgan yechimni bloklash: keyingi iteratsiyada bu yechim qayta topilmasligi uchun
                # Ya'ni, topilgan barcha o'zgaruvchilarning joriy qiymatlarini inkor qilamiz.
                block_clause = []
                for var_name_str in self.vars:
                    z3_bool_var = self.z3_vars[var_name_str]
                    if model.evaluate(z3_bool_var) == True:
                        block_clause.append(Not(z3_bool_var))
                    else:
                        block_clause.append(z3_bool_var)
                s.add(Or(block_clause)) # Or(Not(x1), x2, Not(x3), ...)
                                        # Bu shuni anglatadiki, keyingi yechimda kamida bitta o'zgaruvchining qiymati hozirgidagi teskarisi bo'lishi kerak.

        except Exception as e:
            st.error(f"Z3 solverini ishga tushirishda yoki yechimlarni topishda xato: {e}. Iltimos, tenglamalaringizni va o'zgaruvchilaringizni tekshiring.")
            return None

        return self.prepared_solutions

    def get_javob1_content(self):
        '''
        javob1.txt faylining mazmunini hosil qiladi.
        Har bir y o'zgaruvchisi 1 bo'lgan holatlarda x o'zgaruvchilarini ro'yxatlaydi.
        '''
        output = io.StringIO()
        
        names_to_use = self.display_names if self.display_names else self.vars

        if not self.prepared_solutions:
            output.write("Hech qanday yechim topilmadi.\n")
            return output.getvalue()

        for y_idx in range(self.x_count, len(self.vars)):  # y o'zgaruvchilarini iteratsiya qilish
            y_name = names_to_use[y_idx]
            y_var = self.vars[y_idx]
            output.write(f"\n{y_var} ({y_name}) = 1 bo'lganda x o'zgaruvchilari:\n")
            found_solutions_for_y = False
            for sol in self.prepared_solutions:
                if sol[y_idx] == 1:  # Agar y o'zgaruvchisining qiymati 1 bo'lsa
                    x_names = [names_to_use[i] for i in range(self.x_count) if sol[i] == 1]
                    if x_names:
                        output.write(f"  Yechim: {', '.join(x_names)}\n")
                    else:
                        output.write("  Hech qanday x o'zgaruvchisi 1 emas\n")
                    found_solutions_for_y = True
            if not found_solutions_for_y:
                output.write("  Hech qanday yechim yo'q\n")
        return output.getvalue()

    def get_javob2_content(self):
        '''
        javob2.txt faylining mazmunini hosil qiladi.
        Kamida bitta x o'zgaruvchisi 1 bo'lgan va y o'zgaruvchilaridan 1 bo'lgan holatlarni yozadi.
        '''
        output = io.StringIO()
        
        names_to_use = self.display_names if self.display_names else self.vars

        if not self.prepared_solutions:
            output.write("Hech qanday mos yechim topilmadi.\n")
            return output.getvalue()

        found_any_solution = False
        for sol in self.prepared_solutions:
            # Agar kamida bitta x o'zgaruvchisi 1 bo'lsa
            if any(sol[i] == 1 for i in range(self.x_count)):
                x_names = [names_to_use[i] for i in range(self.x_count) if sol[i] == 1]
                # y o'zgaruvchilaridan qiymati 1 bo'lganlarini topish
                y_names = [names_to_use[i] for i in range(self.x_count, len(self.vars)) if sol[i] == 1]
                if y_names:  # Agar y o'zgaruvchilaridan 1 bo'lganlari bo'lsa
                    for y_name in y_names:
                        # Agar x_names bo'sh bo'lsa, oldiga bo'sh joy qo'ymaslik uchun shart tekshiruvi
                        x_part = f"{', '.join(x_names)} " if x_names else ""
                        output.write(f"{x_part}kasallik belgilari uchraganda {y_name}\n")
                        found_any_solution = True
        if not found_any_solution:
            output.write("Hech qanday mos yechim yo'q\n")
        return output.getvalue()

# --- Streamlit foydalanuvchi interfeysi (UI) ---
st.markdown("<h1 class='main-header'>Mantiqiy Tenglamalar Yechimi (Z3 Solver bilan)</h1>", unsafe_allow_html=True)
st.write("Z3 solver kutubxonasi yordamida mantiqiy tenglamalar tizimi uchun barcha mumkin bo'lgan yechimlarni tezlikda topishga yordam beradi.")

st.markdown("<h3 class='sub-header'>O'zgaruvchilarni kiriting</h3>", unsafe_allow_html=True)

st.markdown("""
    <div class="note-box">
    <b>Izoh:</b> O'zgaruvchi nomlari raqamlar bilan tugashi kerak (masalan, x1, y2).
    </div>
    """, unsafe_allow_html=True)

x_count = st.number_input("x o'zgaruvchilari sonini kiriting:", min_value=0, value=21, step=1, key="x_count_input")
y_count = st.number_input("y o'zgaruvchilari sonini kiriting:", min_value=0, value=5, step=1, key="y_count_input")

col1, col2 = st.columns(2)

default_x_vars = " ".join([f"x{i+1}" for i in range(x_count)])
default_y_vars = " ".join([f"y{i+1}" for i in range(y_count)])

x_vars_input = col1.text_input(f"{x_count} ta x o'zgaruvchisi nomlarini kiriting (bo'sh joy bilan ajratib):", value=default_x_vars, key="x_vars_input")
y_vars_input = col2.text_input(f"{y_count} ta y o'zgaruvchisi nomlarini kiriting (bo'sh joy bilan ajratib):", value=default_y_vars, key="y_vars_input")

var_names = []
if x_vars_input:
    var_names.extend([v.strip() for v in x_vars_input.split() if v.strip()])
if y_vars_input:
    var_names.extend([v.strip() for v in y_vars_input.split() if v.strip()])

st.markdown("<h3 class='sub-header'>Tenglamalarni kiriting</h3>", unsafe_allow_html=True)
st.markdown("""
    <div class="note-box">
    <b>Mantiqiy operatorlar:</b><br>
    <code>!</code> (INKOR) &rarr; <code>Not</code><br>
    <code>+</code> (DIZYUNKSIYA) &rarr; <code>Or</code><br>
    <code>*</code> (KONYUNKSIYA) &rarr; <code>And</code><br>
    <code>=</code> (EKVIVALENTLIK) &rarr; <code>==</code><br>
    <code>-</code> (IMPLIKATSIYA) &rarr; <code>Implies(A, B)</code> (masalan, <code>A - B</code> &rarr; <code>Implies(A, B)</code>)<br>
    Har bir tenglamani yangi qatordan kiriting. <br>
    <br>
    <b>Qo'llab-quvvatlanadigan tenglama formatlari:</b> <br>
    1.  <code>(o'zgaruvchi - (o'zgaruvchi + o'zgaruvchi + ...)) = 1</code> <br>
        <i>Misol:</i> <code>(x1 - (y1 + y3 + y5)) = 1</code> <br>
    2.  <code>((o'zgaruvchi * o'zgaruvchi * ...) = o'zgaruvchi) = 1</code> <br>
        <i>Misol:</i> <code>((x1 * x2 * x3 * x4 * x5) = y1) = 1</code> <br>
    3.  Oddiy tengliklar: <code>o'zgaruvchi = o'zgaruvchi</code> <br>
        <i>Misol:</i> <code>x1 = y1</code> <br>
    4.  Oddiy inkor: <code>!o'zgaruvchi</code> <br>
        <i>Misol:</i> <code>!x1</code> <br>
    5.  Oddiy dizyunksiya: <code>o'zgaruvchi + o'zgaruvchi + ...</code> <br>
        <i>Misol:</i> <code>y1 + y2 + y3</code> <br>
    6.  Oddiy konyunksiya: <code>o'zgaruvchi * o'zgaruvchi * ...</code> <br>
        <i>Misol:</i> <code>x1 * x2 * x3</code> <br>
    </div>
    """, unsafe_allow_html=True)

equations_input_default_val = """(x1 - (y1 + y3 + y5)) = 1
(x2 - (y1 + y4 + y5)) = 1
(x3 - (y1 + y2 + y3 + y5)) = 1
(x4 - (y1 + y2 + y3 + y4 + y5)) = 1
(x5 - (y1 + y3 + y4)) = 1
(x6 - (y2)) = 1
(x7 - (y2)) = 1
(x8 - (y2)) = 1
(x9 - (y2)) = 1
(x10 - (y3)) = 1
(x11 - (y3)) = 1
(x12 - (y3)) = 1
(x13 - (y3)) = 1
(x14 - (y3)) = 1
(x15 - (y4)) = 1
(x16 - (y4)) = 1
(x17 - (y4)) = 1
(x18 - (y3 + y4)) = 1
(x19 - (y5)) = 1
(x20 - (y2)) = 1
(x21 - (y4 + y5)) = 1
((x1 * x2 * x3 * x4 * x5) = y1) = 1
((x3 * x4 * x6 * x7 * x8 * x9 * x20) = y2) = 1
((x1 * x3 * x4 * x5 * x10 * x11 * x12 * x13 * x14 * x18) = y3) = 1
((x2 * x4 * x5 * x15 * x16 * x17 * x18 * x21) = y4) = 1
((x1 * x2 * x3 * x4 * x19 * x21) = y5) = 1"""

equations_input = st.text_area("Mantiqiy tenglamalarni kiriting:", height=400, 
                               value=equations_input_default_val, key="equations_input")

is_set = st.checkbox("Yechimlar to'plamini ko'rsatish", value=True, key="show_sets_checkbox")

if st.button("Yechimlarni hisoblash"):
    # Oldingi natijalarni sessiya holatidan tozalash
    for key in ['solutions', 'solver_instance', 'show_display_names_input']:
        if key in st.session_state:
            del st.session_state[key]

    if not var_names:
        st.error("Iltimos, o'zgaruvchilarni kiriting.")
    elif not equations_input.strip():
        st.error("Iltimos, tenglamalarni kiriting.")
    else:
        start_time = time.time()
        
        with st.spinner('Yechimlar hisoblanmoqda... Bu biroz vaqt olishi mumkin.'):
            try:
                solver = LogSystems(x_count, y_count, var_names, equations_input, is_set)
                solutions = solver.solve() # Z3 yordamida yechimlarni hisoblash
                
                end_time = time.time()
                elapsed_time = end_time - start_time
                
                if solutions is not None:
                    st.session_state['solutions'] = solutions
                    st.session_state['solver_instance'] = solver
                    st.session_state['show_display_names_input'] = True
                    
                    st.markdown(f"<h3 class='sub-header'>Hisoblangan yechimlar soni: {solver.solutions_count}</h3>", unsafe_allow_html=True)
                    st.info(f"Hisoblash vaqti: {elapsed_time:.4f} soniya.")

                    if is_set and solutions:
                        st.markdown("<h3 class='sub-header'>Yechimlar to'plami</h3>", unsafe_allow_html=True)
                        import pandas as pd
                        df = pd.DataFrame(solutions, columns=var_names)
                        st.dataframe(df.style.set_table_styles([
                            {'selector': 'th', 'props': [('background-color', '#f2f2f2'), ('color', '#333'), ('font-weight', 'bold'), ('padding', '10px'), ('border-bottom', '2px solid #ddd')]},
                            {'selector': 'td', 'props': [('padding', '8px'), ('border-bottom', '1px solid #eee')]}
                        ]), use_container_width=True)
                    elif not solutions:
                        st.info("Hisoblangan yechimlar yo'q.")
                else:
                    st.warning("Yechimlar topilmadi yoki hisoblashda xato yuz berdi. Iltimos, yuqoridagi xabarlarni tekshiring.")
            except ValueError as e:
                st.error(f"Kiritish xatosi: {e}")
            except Exception as e:
                st.error(f"Kutilmagan xato yuz berdi: {e}")

if 'show_display_names_input' in st.session_state and st.session_state['show_display_names_input']:
    st.markdown("<h3 class='sub-header'>Fayllar uchun tushunarli nomlar kiriting</h3>", unsafe_allow_html=True)
    st.markdown("""
        <div class="note-box">
        Har bir o'zgaruvchi uchun bitta qatorda mos nomni kiriting. Masalan, <code>x1</code> uchun <code>Harorat</code>.
        Agar bo'sh qoldirsangiz, o'zgaruvchining asl nomi ishlatiladi.
        </div>
        """, unsafe_allow_html=True)

    current_solver = st.session_state.get('solver_instance')
    if current_solver:
        if not current_solver.display_names or len(current_solver.display_names) != len(current_solver.vars):
            current_solver.display_names = [""] * len(current_solver.vars)

        display_name_inputs = {}
        for i, var in enumerate(current_solver.vars):
            display_name_inputs[var] = st.text_input(f"'{var}' uchun tushunarli nom:", key=f"display_name_{var}", 
                                                      value=current_solver.display_names[i])

        if st.button("Fayllarni yaratish va yuklab olish"):
            current_solver.display_names = [display_name_inputs[var].strip() if display_name_inputs[var].strip() else var for var in current_solver.vars]
            
            javob1_content = current_solver.get_javob1_content()
            st.download_button(
                label="javob1.txt faylini yuklab olish",
                data=javob1_content,
                file_name="javob1.txt",
                mime="text/plain",
                key="download_javob1"
            )

            javob2_content = current_solver.get_javob2_content()
            st.download_button(
                label="javob2.txt faylini yuklab olish",
                data=javob2_content,
                file_name="javob2.txt",
                mime="text/plain",
                key="download_javob2"
            )
            st.success("Fayllar muvaffaqiyatli yaratildi va yuklab olish uchun tayyor!")
    else:
        st.warning("Yechimlar hali hisoblanmagan. Iltimos, avval 'Yechimlarni hisoblash' tugmasini bosing.")

st.markdown("---")
st.markdown("Sizga yordam bera olganimdan xursandman!")
