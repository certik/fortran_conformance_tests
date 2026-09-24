module expr_overall_defined_m
  implicit none
  interface operator(.combine.)
    module procedure combine
  end interface
contains
  integer function combine(left, right)
    integer, intent(in) :: left, right
    combine = 70 + left + 2*right
  end function combine
end module expr_overall_defined_m
program expr_overall_forms
  use expr_overall_defined_m
  implicit none
  integer :: checks, left, right, scalar_result
  integer :: a(2), b(2), array_result(2)
  checks=0
  scalar_result = (2+3)
  if (scalar_result /= 5) error stop 'EOF:paren'
  checks=checks+1
  left = 8
  right = 9
  if (left + right /= 17) error stop 'EOF:scalar'
  checks=checks+1
  a = [1,2]
  b = [3,4]
  array_result = a + b
  if (any(array_result /= [4,6])) error stop 'EOF:array'
  checks=checks+1
  if (4 * 5 /= 20) error stop 'EOF:intrinsic'
  checks=checks+1
  if ((3 .combine. 4) /= 81) error stop 'EOF:defined'
  checks=checks+1
  if ((1+2)*(3+4) /= 21) error stop 'EOF:nested'
  checks=checks+1
  if (checks /= 6) error stop 'EOF:checks'
  write(*,'(a)') 'EXPRESSIONS OVERALL FORMS OK'
end program expr_overall_forms
