program expr_primary_core_forms
  implicit none
  type :: pair
    integer :: a, b
  end type pair
  integer :: checks, designator_value, array_value(2), function_value, parenthesized_value, conditional_value
  type(pair) :: constructed
  checks=0
  if (19 /= 19) error stop 'EPC:literal'
  checks=checks+1
  designator_value = 23
  if (designator_value /= 23) error stop 'EPC:designator'
  checks=checks+1
  array_value = [3,5]
  if (any(array_value /= [3,5])) error stop 'EPC:array'
  checks=checks+1
  constructed = pair(7,11)
  if (constructed%b /= 11) error stop 'EPC:structure'
  checks=checks+1
  function_value = make_value(4)
  if (function_value /= 29) error stop 'EPC:function'
  checks=checks+1
  parenthesized_value = (2+6)
  if (parenthesized_value /= 8) error stop 'EPC:parenthesized'
  checks=checks+1
  conditional_value = (.true. ? 31 : 41)
  if (conditional_value /= 31) error stop 'EPC:conditional'
  checks=checks+1
  if (checks /= 7) error stop 'EPC:checks'
  write(*,'(a)') 'EXPRESSIONS PRIMARY CORE FORMS OK'
contains
  integer function make_value(x)
    integer, intent(in) :: x
    make_value = 25 + x
  end function make_value
end program expr_primary_core_forms
