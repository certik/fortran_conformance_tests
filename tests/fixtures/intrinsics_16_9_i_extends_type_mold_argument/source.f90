program i169i_extends_type_arguments
  implicit none
  type :: parent
    integer :: p = 1
  end type parent
  type, extends(parent) :: child
    integer :: c = 2
  end type child
  type, extends(parent) :: sibling
    integer :: s = 3
  end type sibling
  type(parent) :: p
  type(child) :: c
  class(*), allocatable :: unlimited_a
  class(*), allocatable :: unlimited_mold
  allocate(child :: unlimited_a)
  allocate(parent :: unlimited_mold)
  call require_true('a may be unlimited polymorphic allocated child', extends_type_of(unlimited_a, p))
  call require_true('mold may be unlimited polymorphic allocated parent', extends_type_of(c, unlimited_mold))
  write(*,'(a)') 'INTRINSICS 16.9.I EXTENDS TYPE MOLD ARGUMENT OK'
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
end program i169i_extends_type_arguments
