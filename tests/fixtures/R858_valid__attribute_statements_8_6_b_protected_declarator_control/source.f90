module attribute_statements_protected_decl_m
  implicit none
  integer :: a(2) = [3, 4]
  protected :: a
contains
  subroutine set_a(v)
    integer, intent(in) :: v
    a(1) = v
  end subroutine
end module
program main
  use attribute_statements_protected_decl_m, only: a, set_a
  implicit none
  call set_a(9)
  if (a(1) /= 9) error stop 1
  if (a(2) /= 4) error stop 2
  write(*,'(a)') 'ATTRIBUTE STATEMENTS PROTECTED DECLARATOR CONTROL OK'
end program
