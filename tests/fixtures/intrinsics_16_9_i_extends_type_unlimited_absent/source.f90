program i169i_extends_type_unlimited_absent
  implicit none
  type :: parent
    integer :: p = 1
  end type parent
  type, extends(parent) :: child
    integer :: c = 2
  end type child
  type(parent) :: p
  class(*), allocatable :: mold_absent
  class(*), allocatable :: a_absent
  class(*), pointer :: a_pointer
  nullify(a_pointer)
  call require_true('unallocated unlimited mold gives true', extends_type_of(p, mold_absent))
  call require_false('unallocated unlimited a gives false', extends_type_of(a_absent, p))
  call require_false('disassociated unlimited a pointer gives false', extends_type_of(a_pointer, p))
  write(*,'(a)') 'INTRINSICS 16.9.I EXTENDS TYPE UNLIMITED ABSENT OK'
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
end program i169i_extends_type_unlimited_absent
