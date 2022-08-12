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
})
