module procedure_reference_15_5_1_defined_m
  implicit none
  type box
    integer :: value = -9
  end type
  interface operator(.join.)
    module procedure join_values
  end interface
  interface operator(.other.)
    module procedure other_values
  end interface
  interface assignment(=)
    module procedure assign_integer
  end interface
contains
  integer function join_values(a, b)
    integer, intent(in) :: a, b
    join_values = 10 * a + b
  end function
  integer function other_values(a, b)
    integer, intent(in) :: a, b
    other_values = 10 * b + a
  end function
  subroutine assign_integer(lhs, rhs)
    type(box), intent(out) :: lhs
    integer, intent(in) :: rhs
    lhs%value = rhs + 5
  end subroutine
end module procedure_reference_15_5_1_defined_m

program procedure_reference_15_5_1_defined
  use procedure_reference_15_5_1_defined_m
  implicit none
  type(box) :: item
  integer :: op_value, checks
  checks = 0
  op_value = -1
  op_value = 3 .join. 4
  if (op_value /= 34) error stop 601
  checks = checks + 1
  item%value = -9
  item = 12
  if (item%value /= 17) error stop 602
  checks = checks + 1
  if (checks /= 2) error stop 699
  print '(a)', 'PROCEDURE REFERENCE DEFINED FORMS OK'
end program procedure_reference_15_5_1_defined
