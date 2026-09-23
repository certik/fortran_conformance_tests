module protected_attribute_entities
  implicit none
  integer, protected :: scalar = 5
  integer, pointer, protected :: data_ptr => null()
  abstract interface
    integer function op_i(v)
      integer, intent(in) :: v
    end function
  end interface
  procedure(op_i), pointer, protected :: proc => null()
contains
  integer function plus_one(v)
    integer, intent(in) :: v
    plus_one = v + 1
  end function
  subroutine bind_proc()
    proc => plus_one
  end subroutine
  subroutine bind_data(target)
    integer, target, intent(inout) :: target
    data_ptr => target
  end subroutine
end module
program main
  use protected_attribute_entities, only: scalar, data_ptr, proc, bind_proc, bind_data
  implicit none
  integer, target :: local
  local = 37
  if (scalar /= 5) error stop 1
  if (associated(data_ptr)) error stop 2
  call bind_data(local)
  if (.not. associated(data_ptr, local)) error stop 3
  call bind_proc()
  if (.not. associated(proc)) error stop 4
  if (proc(41) /= 42) error stop 5
  write(*,'(a)') 'PROTECTED ATTRIBUTE ENTITY ADMISSION OK'
end program
