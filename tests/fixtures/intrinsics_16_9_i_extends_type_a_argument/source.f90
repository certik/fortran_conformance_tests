program i169i_extends_type_a_argument
  implicit none
  type :: parent
    integer :: p = 1
  end type parent
  type, extends(parent) :: child
    integer :: c = 2
  end type child
  type(child) :: c
  class(*), allocatable :: unlimited_a
  allocate(child :: unlimited_a)
  call require_true('a may be unlimited polymorphic allocated child', extends_type_of(unlimited_a, c))
  write(*,'(a)') 'INTRINSICS 16.9.I EXTENDS TYPE A ARGUMENT OK'
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
end program i169i_extends_type_a_argument
