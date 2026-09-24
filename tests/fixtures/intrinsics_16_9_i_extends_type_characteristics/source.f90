program i169i_extends_type_characteristics
  implicit none
  type :: parent
    integer :: p = 1
  end type parent
  type, extends(parent) :: child
    integer :: c = 2
  end type child
  integer, parameter :: alt_logical_kind = merge(1, 4, kind(.false.) /= 1)
  type(parent) :: p
  type(child) :: c
  call require_true('extends_type_of result default logical', &
       kind(extends_type_of(c, p)) == kind(.false.))
  call require_true('extends_type_of result logical value', &
       extends_type_of(c, p))
  call require_true('extends_type_of result scalar', rank(extends_type_of(c, p)) == 0)
  write(*,'(a)') 'INTRINSICS 16.9.I EXTENDS TYPE CHARACTERISTICS OK'
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
end program i169i_extends_type_characteristics
