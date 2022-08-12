/*
aquaorder
Copyright (C) 2022  schnusch

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

declare interface String {
    lpad(this: string, length: number, char: string): string
}

String.prototype.lpad = function(this: string, length: number, char: string): string {
    var s = this
    while(s.length < length) {
        s = char + s
    }
    return s
}

function find_date_picker(): HTMLInputElement {
    const date_pickers = document.getElementsByName("date")
    if(date_pickers.length == 0 || !(date_pickers[0] instanceof HTMLInputElement)) {
        throw "date picker not found"
    }
    return date_pickers[0]
}

function add_cell(
    tr: HTMLElement,
    td_attributes: {[key: string]: string},
    input_attributes: {[key: string]: string},
): HTMLInputElement {
    const td = document.createElement("td")
    for(const attr in td_attributes) {
        td.setAttribute(attr, td_attributes[attr])
    }
    const input = td.appendChild(document.createElement("input"))
    input.setAttribute("type", "text")
    for(const attr in input_attributes) {
        input.setAttribute(attr, input_attributes[attr])
    }
    tr.appendChild(td)
    return input
}

function add_row(table: HTMLTableElement, index: number, even_odd: "even"|"odd", suppliers: string[]): void {
    let first = true
    for(const supplier of suppliers) {
        const tr = document.createElement("tr")
        add_cell(tr, {"class": "supplier"}, {
            "type": "radio",
            "tabindex": "-1",
            "name": `${index}_supplier`,
            "value": supplier,
        })
        add_cell(tr, {"class": "id"},   {"name": `${index}_${supplier}_id`,   "tabindex": "-1"})
        add_cell(tr, {"class": "name"}, {"name": `${index}_${supplier}_name`, "tabindex": "-1"})
        add_cell(tr, {"class": "size"}, {"name": `${index}_${supplier}_size`, "tabindex": "-1"})
        if(first) {
            add_cell(
                tr,
                {"rowspan": String(suppliers.length), "class": "amount"},
                {"type": "number", "name": `${index}_amount`, "min": "0"},
            ).scrollIntoView()
            tr.classList.add("first")
        }
        tr.classList.add(even_odd)
        tr.classList.add(supplier)
        table.appendChild(tr)
        if(first) {
            first = false
        }
    }
}

function get_all_suppliers(): string[] {
    const suppliers = []
    for(const supplier_input of document.querySelectorAll('[name$="_supplier"]')) {
        const m = supplier_input.getAttribute("name")?.match(/^\d+_supplier$/)
        const supplier = supplier_input.getAttribute("value")
        if(m && supplier && suppliers.indexOf(supplier) < 0) {
            suppliers.push(supplier)
        }
    }
    return suppliers.sort()
}

function get_highest_index(): number {
    let index = -1
    for(const amount_input of document.querySelectorAll('[name$="_amount"]')) {
        const m = amount_input.getAttribute("name")?.match(/^(\d+)_amount$/)
        if(m) {
            const i = parseInt(m[1])
            if(i > index) {
                index = i
            }
        }
    }
    return index
}

function get_even_odd(table: HTMLTableElement): "even"|"odd" {
    const trs = table.rows
    if(trs.length == 0 || trs[trs.length - 1].classList.contains("even")) {
        return "odd"
    } else {
        return "even"
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const date_picker = find_date_picker()
    console.log(date_picker)
    const date = new Date()
    if(date.getHours() >= 14) {
        date.setDate(date.getDate() + 1)
    }
    date.setDate(date.getDate() + 1)
    date_picker.setAttribute("value", `${
        String(date.getFullYear()).lpad(4, "0")
    }-${
        String(date.getMonth() + 1).lpad(2, "0")
    }-${
        String(date.getDate()).lpad(2, "0")
    }`)

    const table = document.querySelector("table")
    const add_line_button = document.getElementById("add_line")
    if(table && add_line_button) {
        const suppliers = get_all_suppliers()
        add_line_button.addEventListener("click", () => {
            add_row(table, get_highest_index() + 1, get_even_odd(table), suppliers)
        })
    }
})
