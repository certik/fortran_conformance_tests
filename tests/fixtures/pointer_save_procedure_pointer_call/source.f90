program procedure_pointer_call
  implicit none
  abstract interface
    integer function unary(x)
      integer, intent(in) :: x
    end function unary
  end interface
  procedure(unary), pointer :: fp
  integer :: checks
  checks = 0
  nullify(fp)
  if (associated(fp)) error stop
  checks = checks + 1
  fp => add_eleven
  if (.not. associated(fp)) error stop
  checks = checks + 1
  if (fp(4) /= 15) error stop
  checks = checks + 1
  if (checks /= 3) error stop
  print '(a)', 'PROCEDURE POINTER CALL OK'
contains
  integer function add_eleven(x)
    integer, intent(in) :: x
    add_eleven = x + 11
  end function add_eleven
  integer function add_twelve(x)
    integer, intent(in) :: x
    add_twelve = x + 12
  end function add_twelve
end program procedure_pointer_call
