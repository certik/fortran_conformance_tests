program p
implicit none
type :: root
    integer :: payload
end type
type, extends(root) :: child
    integer :: child_marker
end type
type, extends(child) :: grand
    integer :: grand_marker
end type
type, extends(root) :: sibling
integer :: sibling_marker
end type
type :: other
integer :: payload
end type
type(root) :: root_value
type(child) :: child_value
type(grand) :: grand_value
type(sibling) :: sibling_value
type(other) :: other_value
logical :: actual(5,5)
root_value%payload = 11
child_value%payload = 13
child_value%child_marker = 41
grand_value%payload = 17
grand_value%child_marker = 43
grand_value%grand_marker = 47
sibling_value%payload = 19
sibling_value%sibling_marker = 53
other_value%payload = 23
actual(1,1) = extends_type_of(root_value, root_value)
actual(1,2) = extends_type_of(root_value, child_value)
actual(1,3) = extends_type_of(root_value, grand_value)
actual(1,4) = extends_type_of(root_value, sibling_value)
actual(1,5) = extends_type_of(root_value, other_value)
actual(2,1) = extends_type_of(child_value, root_value)
actual(2,2) = extends_type_of(child_value, child_value)
actual(2,3) = extends_type_of(child_value, grand_value)
actual(2,4) = extends_type_of(child_value, sibling_value)
actual(2,5) = extends_type_of(child_value, other_value)
actual(3,1) = extends_type_of(grand_value, root_value)
actual(3,2) = extends_type_of(grand_value, child_value)
actual(3,3) = extends_type_of(grand_value, grand_value)
actual(3,4) = extends_type_of(grand_value, sibling_value)
actual(3,5) = extends_type_of(grand_value, other_value)
actual(4,1) = extends_type_of(sibling_value, root_value)
actual(4,2) = extends_type_of(sibling_value, child_value)
actual(4,3) = extends_type_of(sibling_value, grand_value)
actual(4,4) = extends_type_of(sibling_value, sibling_value)
actual(4,5) = extends_type_of(sibling_value, other_value)
actual(5,1) = extends_type_of(other_value, root_value)
actual(5,2) = extends_type_of(other_value, child_value)
actual(5,3) = extends_type_of(other_value, grand_value)
actual(5,4) = extends_type_of(other_value, sibling_value)
actual(5,5) = extends_type_of(other_value, other_value)
if (any(actual(1,:) .neqv. [.true.,.false.,.false.,.false.,.false.])) error stop 1
if (any(actual(2,:) .neqv. [.true.,.true.,.false.,.false.,.false.])) error stop 2
if (any(actual(3,:) .neqv. [.true.,.true.,.true.,.false.,.false.])) error stop 3
if (any(actual(4,:) .neqv. [.true.,.false.,.false.,.true.,.false.])) error stop 4
if (any(actual(5,:) .neqv. [.false.,.false.,.false.,.false.,.true.])) error stop 5
end program p
