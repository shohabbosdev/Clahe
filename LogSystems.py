import streamlit as st
import re
import io

class LogSystems:
    '''
    Mantiqiy tenglamalar yoki mantiqiy tenglamalar tizimini yechuvchi klass.
    Ajoyib interfeys bilan Streamlit orqali ishlaydi.
    '''
    def __init__(self, x_count, y_count, var_names, equations_str, is_set=True):
        self.solutions_count = 0  # Tenglama (tizim) yechimlari soni
        self.function = ""  # Mantiqiy funksiya
        self.vars = var_names  # Funkciyadagi o'zgaruvchilar
        self.display_names = []  # Foydalanuvchi kiritgan mos nomlar
        self.is_set = is_set  # O'zgaruvchilar to'plamlarini chiqarish kerakmi
        self.x_count = x_count  # x o'zgaruvchilari soni
        self.y_count = y_count  # y o'zgaruvchilari soni
        self.equations_str = equations_str # Tenglamalar matn ko'rinishida
        self.raw_equations = [] # Foydalanuvchi kiritgan dastlabki tenglamalar
        self.prepared_solutions = [] # eval qilingan barcha yechimlar

    def prepare_function(self):
        '''
        Foydalanuvchi kiritgan tenglamalarni eval() qilish uchun tayyorlaydi.
        '''
        if not self.vars:
            raise ValueError("O'zgaruvchilar ro'yxati bo'sh. Iltimos, o'zgaruvchilarni kiriting.")
        
        # Tenglamalarni qatorlarga ajratish va bo'sh qatorlarni olib tashlash
        self.raw_equations = [eq.strip() for eq in self.equations_str.split('\n') if eq.strip()]
        
        if not self.raw_equations:
            raise ValueError("Tenglamalar kiritilmagan. Iltimos, kamida bitta tenglama kiriting.")

        # Kiritilgan o'zgaruvchilarni tekshirish
        input_vars = set()
        for eq in self.raw_equations:
            found_vars = re.findall(r'[a-zA-Z]+[0-9]*', eq) # Kichik harfli o'zgaruvchilarni ham topish uchun regexni yangiladim
            input_vars.update(found_vars)

        if not set(self.vars).issuperset(input_vars): # Tenglamalarda kiritilmagan o'zgaruvchilar borligini tekshirish
            missing_vars_in_input = input_vars - set(self.vars)
            if missing_vars_in_input:
                raise ValueError(f"Kiritilgan tenglamalardagi ba'zi o'zgaruvchilar ({', '.join(missing_vars_in_input)}) yuqorida ko'rsatilgan o'zgaruvchilar ro'yxatida ({', '.join(self.vars)}) mavjud emas.")
        
        fun_parts = ['1']
        for eq in self.raw_equations:
            # Bo'sh joylarni olib tashlash
            eq_cleaned = eq.replace(' ', '')
            
            # Mantiqiy operatorlarni almashtirish
            eq_cleaned = eq_cleaned.replace('!', " not ")  # Inkor
            eq_cleaned = eq_cleaned.replace('+', " or ")   # Dizyunksiya
            eq_cleaned = eq_cleaned.replace('*', " and ")  # Konyunksiya
            eq_cleaned = eq_cleaned.replace('=', " == ")   # Ekvivalentlik
            eq_cleaned = eq_cleaned.replace('-', " <= ")   # Implikatsiya (misol uchun: A -> B, A <= B)

            # O'zgaruvchilarni "set[index]" formatiga almashtirish
            # O'zgaruvchilarni uzunligiga qarab teskari tartibda almashtirish,
            # masalan "x10" "x1" dan oldin almashtirilishi kerak
            sorted_vars = sorted(self.vars, key=len, reverse=True)
            for var in sorted_vars:
                if var in eq_cleaned:
                    eq_cleaned = eq_cleaned.replace(var, f"set[{self.vars.index(var)}]")

            fun_parts.append(f"({eq_cleaned})")
        
        # Barcha tenglamalarni "and" operatori bilan bog'lash
        self.function = " and ".join(fun_parts)

    def generate_set(self, number):
        '''
        Nabor raqamining ikkilik ko'rinishiga asoslangan o'zgaruvchilar to'plamini yaratish metodi.
        '''
        s = []
        for i in range(len(self.vars)):
            s.append((number >> i) & 1) # Bitwise operatsiyalardan foydalanib samaraliroq
        return s[::-1] # Teskari tartibda qaytarish

    def solve(self):
        '''
        Funkciyadagi barcha mumkin bo'lgan o'zgaruvchi qiymatlarini ko'rib chiqish metodi.
        '''
        self.solutions_count = 0
        self.prepared_solutions = []
        
        try:
            self.prepare_function()
        except ValueError as e:
            st.error(f"Tenglama yoki o'zgaruvchi xatosi: {e}")
            return

        sets_to_check = 2**len(self.vars)  # Barcha mumkin bo'lgan o'zgaruvchilar to'plami soni

        for number in range(sets_to_check):
            set = self.generate_set(number)
            try:
                if eval(self.function):
                    self.solutions_count += 1
                    self.prepared_solutions.append(set)
            except Exception as e:
                st.error(f"Tenglamani hisoblashda xato yuz berdi. Tekshiring: {e}\n"
                         f"Hisoblanayotgan funksiya: `{self.function}`\n"
                         f"Hozirgi to'plam: `{set}`")
                return

        return self.prepared_solutions

    def get_javob1_content(self):
        '''
        javob1.txt faylining mazmunini hosil qiladi.
        '''
        output = io.StringIO()
        
        # Agar display_names bo'sh bo'lsa, avtomatik ravishda vars dan foydalanish
        names_to_use = self.display_names if self.display_names else self.vars

        for y_idx in range(self.x_count, len(self.vars)):  # y o'zgaruvchilari
            y_name = names_to_use[y_idx]
            y_var = self.vars[y_idx]
            output.write(f"\n{y_var} ({y_name}) = 1 bo'lganda x o'zgaruvchilari:\n")
            found_solutions_for_y = False
            for sol in self.prepared_solutions:
                if sol[y_idx] == 1:  # y o'zgaruvchisi 1 bo'lsa
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
        '''
        output = io.StringIO()
        
        # Agar display_names bo'sh bo'lsa, avtomatik ravishda vars dan foydalanish
        names_to_use = self.display_names if self.display_names else self.vars

        found_any_solution = False
        for sol in self.prepared_solutions:
            # Kamida bitta x o'zgaruvchisi 1 bo'lsa
            if any(sol[i] == 1 for i in range(self.x_count)):
                x_names = [names_to_use[i] for i in range(self.x_count) if sol[i] == 1]
                # y o'zgaruvchilaridan qiymati 1 bo'lganlarini topish
                y_names = [names_to_use[i] for i in range(self.x_count, len(self.vars)) if sol[i] == 1]
                if y_names:  # Agar y o'zgaruvchilaridan 1 bo'lganlari bo'lsa
                    for y_name in y_names:
                        output.write(f"{', '.join(x_names)} kasallik belgilari uchraganda {y_name}\n")
                        found_any_solution = True
        if not found_any_solution:
            output.write("Hech qanday mos yechim yo'q\n")
        return output.getvalue()

# Streamlit ilovasi
st.set_page_config(layout="centered", page_title="Mantiqiy tenglamalar yechimi")


st.markdown("<h1 class='main-header'>Mantiqiy tenglamalar yechimi</h1>", unsafe_allow_html=True)
st.write("Mantiqiy tenglamalar tizimi uchun barcha mumkin bo'lgan yechimlarni topishga yordam beradi.")

st.markdown("<h3 class='sub-header'>O'zgaruvchilarni kiriting</h3>", unsafe_allow_html=True)

st.markdown("""
    <div class="note-box">
    <b>Izoh:</b> O'zgaruvchi nomlari raqamlar bilan tugashi kerak (masalan, x1, y2).
    </div>
    """, unsafe_allow_html=True)

x_count = st.number_input("x o'zgaruvchilari sonini kiriting (masalan, 6 uchun x1, x2, ..., x6):", min_value=0, value=0, step=1, key="x_count_input")
y_count = st.number_input("y o'zgaruvchilari sonini kiriting (masalan, 8 uchun y1, y2, ..., y8):", min_value=0, value=0, step=1, key="y_count_input")

col1, col2 = st.columns(2)

x_vars_input = col1.text_input(f"{x_count} ta x o'zgaruvchisi nomlarini kiriting (bo'sh joy bilan ajratib):", value=" ".join([f"x{i+1}" for i in range(x_count)]), key="x_vars_input")
y_vars_input = col2.text_input(f"{y_count} ta y o'zgaruvchisi nomlarini kiriting (bo'sh joy bilan ajratib):", value=" ".join([f"y{i+1}" for i in range(y_count)]), key="y_vars_input")

var_names = []
if x_vars_input:
    var_names.extend(x_vars_input.split())
if y_vars_input:
    var_names.extend(y_vars_input.split())

st.markdown("<h3 class='sub-header'>Tenglamalarni kiriting</h3>", unsafe_allow_html=True)
st.markdown("""
    <div class="note-box">
    <b>Mantiqiy operatorlar:</b><br>
    <code>!</code> (INKOR) &rarr; <code>not</code><br>
    <code>+</code> (DIZYUNKSIYA) &rarr; <code>or</code><br>
    <code>*</code> (KONYUNKSIYA) &rarr; <code>and</code><br>
    <code>=</code> (EKVIVALENTLIK) &rarr; <code>==</code><br>
    <code>-</code> (IMPLIKATSIYA) &rarr; <code><=</code> (masalan, <code>A - B</code> &rarr; <code>A <= B</code>)<br>
    Har bir tenglamani yangi qatordan kiriting.
    <br><br>
    <b>Misol:</b><br>
    <code>(x1 + y1) = 0</code><br>
    <code>!(x2 * y2) - x1 = 1</code>
    </div>
    """, unsafe_allow_html=True)

equations_input = st.text_area("Mantiqiy tenglamalarni kiriting:", height=200, 
                               value="""(x1 + y1) = 0
(x2 * y2) = 1""", key="equations_input")

is_set = st.checkbox("Yechimlar to'plamini ko'rsatish", value=True, key="show_sets_checkbox")

if st.button("Yechimlarni hisoblash"):
    if not var_names:
        st.error("Iltimos, o'zgaruvchilarni kiriting.")
    elif not equations_input.strip():
        st.error("Iltimos, tenglamalarni kiriting.")
    else:
        try:
            solver = LogSystems(x_count, y_count, var_names, equations_input, is_set)
            solutions = solver.solve()
            
            if solutions is not None: # Agar xato bo'lmasa
                st.session_state['solutions'] = solutions
                st.session_state['solver_instance'] = solver # Solver instanceni saqlash
                st.session_state['show_display_names_input'] = True
                
                st.markdown(f"<h3 class='sub-header'>Hisoblangan yechimlar soni: {solver.solutions_count}</h3>", unsafe_allow_html=True)

                if is_set and solutions:
                    st.markdown("<h3 class='sub-header'>Yechimlar to'plami</h3>", unsafe_allow_html=True)
                    # Yechimlarni DataFrame ko'rinishida ko'rsatish
                    import pandas as pd
                    df = pd.DataFrame(solutions, columns=var_names)
                    st.dataframe(df.style.set_table_styles([
                        {'selector': 'th', 'props': [('background-color', '#f2f2f2'), ('color', '#333'), ('font-weight', 'bold'), ('padding', '10px'), ('border-bottom', '2px solid #ddd')]},
                        {'selector': 'td', 'props': [('padding', '8px'), ('border-bottom', '1px solid #eee')]}
                    ]), use_container_width=True)
                elif not solutions:
                    st.info("Hisoblangan yechimlar yo'q.")
        except ValueError as e:
            st.error(f"Kiritish xatosi: {e}")
        except Exception as e:
            st.error(f"Kutilmagan xato yuz berdi: {e}")

# Yechimlar hisoblangandan keyin 'Tushunarli nomlar' qismini ko'rsatish
if 'show_display_names_input' in st.session_state and st.session_state['show_display_names_input']:
    st.markdown("<h3 class='sub-header'>Fayllar uchun tushunarli nomlar kiriting</h3>", unsafe_allow_html=True)
    st.markdown("""
        <div class="note-box">
        Har bir o'zgaruvchi uchun bitta qatorda mos nomni kiriting. Masalan, <code>x1</code> uchun <code>Harorat</code>.
        Agar bo'sh qoldirsangiz, asl o'zgaruvchi nomi ishlatiladi.
        </div>
        """, unsafe_allow_html=True)

    current_solver = st.session_state['solver_instance']
    display_name_inputs = {}
    for i, var in enumerate(current_solver.vars):
        display_name_inputs[var] = st.text_input(f"'{var}' uchun tushunarli nom:", key=f"display_name_{var}", 
                                                  value=current_solver.display_names[i] if i < len(current_solver.display_names) else "")

    if st.button("Fayllarni yaratish va yuklab olish"):
        # Display nomlarini yangilash
        current_solver.display_names = [display_name_inputs[var] if display_name_inputs[var].strip() else var for var in current_solver.vars]
        
        # javob1.txt mazmunini olish
        javob1_content = current_solver.get_javob1_content()
        st.download_button(
            label="javob1.txt faylini yuklab olish",
            data=javob1_content,
            file_name="javob1.txt",
            mime="text/plain",
            key="download_javob1"
        )

        # javob2.txt mazmunini olish
        javob2_content = current_solver.get_javob2_content()
        st.download_button(
            label="javob2.txt faylini yuklab olish",
            data=javob2_content,
            file_name="javob2.txt",
            mime="text/plain",
            key="download_javob2"
        )
        st.success("Fayllar muvaffaqiyatli yaratildi va yuklab olish uchun tayyor!")

st.markdown("---")
st.markdown("Sizga yordam bera olganimdan xursandman!")
