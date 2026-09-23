module protected_attribute_pointer_query_m
  implicit none
  integer, target :: store = 19
  integer, pointer, protected :: data_ptr => null()
  abstract interface
    integer function op_i(v)
      integer, intent(in) :: v
    end function
  end interface
  procedure(op_i), pointer, protected :: proc => null()
contains
  integer function times_two(v)
    integer, intent(in) :: v
    times_two = v * 2
  end function
  subroutine bind_all()
    data_ptr => store
    proc => times_two
  end subroutine
end module
program main
  use protected_attribute_pointer_query_m, only: data_ptr, proc, store, bind_all
  implicit none
  call bind_all()
  if (.not. associated(data_ptr, store)) error stop 1
  if (.not. associated(proc)) error stop 2
  if (proc(21) /= 42) error stop 3
  write(*,'(a)') 'PROTECTED ATTRIBUTE POINTER QUERY CONTROL OK'
end program
