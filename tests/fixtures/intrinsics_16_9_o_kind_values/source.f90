program i169o_kind_values
  implicit none
  integer, parameter :: wide_int_k = selected_int_kind(18)
  integer(kind=wide_int_k) :: wide_integer = 123_wide_int_k
  real(kind=kind(0.0d0)) :: double_real = 1.5d0
  complex(kind=kind(0.0d0)) :: double_complex = (2.0d0, -3.0d0)
  logical :: logical_value = .true.
  character(len=5) :: char_value = 'HELLO'
  call require_true('kind returns integer kind parameter', kind(wide_integer) == wide_int_k)
  call require_true('kind returns real kind parameter', kind(double_real) == kind(0.0d0))
  call require_true('kind returns complex kind parameter', kind(double_complex) == kind((0.0d0, 0.0d0)))
  call require_true('kind returns logical kind parameter', logical_value .and. kind(logical_value) == kind(.true.))
  call require_true('kind returns character kind parameter independent of length', &
      len(char_value) == 5 .and. kind(char_value) == kind('A'))
  write(*,'(a)') 'INTRINSICS 16.9.O KIND VALUES OK'
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
end program i169o_kind_values
