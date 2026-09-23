module protected_attribute_proc_call_m
  implicit none
  abstract interface
    integer function op_i(v)
      integer, intent(in) :: v
    end function
  end interface
  procedure(op_i), pointer, protected :: proc => null()
contains
  integer function add_three(v)
    integer, intent(in) :: v
    add_three = v + 3
  end function
  subroutine bind_proc()
    proc => add_three
  end subroutine
end module
program main
  use protected_attribute_proc_call_m, only: proc, bind_proc
  implicit none
  call bind_proc()
  if (.not. associated(proc)) error stop 1
  if (proc(39) /= 42) error stop 2
  write(*,'(a)') 'PROTECTED ATTRIBUTE PROCEDURE CALL CONTROL OK'
end program
