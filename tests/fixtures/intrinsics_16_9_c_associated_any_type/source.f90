module i169c_assoc_any_type_mod
  implicit none
  type :: payload
    integer :: tag
  end type payload
  abstract interface
    integer function int_fun(x)
      integer, intent(in) :: x
    end function int_fun
  end interface
contains
  integer function proc_target(x)
    integer, intent(in) :: x
    proc_target = x + 3
  end function proc_target
end module i169c_assoc_any_type_mod
program i169c_associated_any_type
  use i169c_assoc_any_type_mod
  implicit none
  integer, target :: int_target = 5
  real, target :: real_target = 2.0
  type(payload), target :: derived_target
  integer, pointer :: int_pointer
  real, pointer :: real_pointer
  type(payload), pointer :: derived_pointer
  procedure(int_fun), pointer :: procedure_pointer
  derived_target%tag = 19
  int_pointer => int_target
  real_pointer => real_target
  derived_pointer => derived_target
  procedure_pointer => proc_target
  call require_true('integer data pointer admitted', associated(int_pointer))
  call require_true('real data pointer admitted', associated(real_pointer))
  call require_true('derived data pointer admitted', associated(derived_pointer))
  call require_true('procedure pointer admitted', associated(procedure_pointer))
  write(*,'(a)') 'INTRINSICS 16.9.C ASSOCIATED ANY TYPE OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
end program i169c_associated_any_type
