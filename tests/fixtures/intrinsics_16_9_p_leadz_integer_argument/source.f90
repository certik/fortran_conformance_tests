program i169p_leadz_integer_argument
  implicit none
  integer :: integer_actual
  integer_actual = 0
  call require_true('leadz accepts integer actual', leadz(integer_actual) == bit_size(integer_actual))
  write(*,'(a)') 'INTRINSICS 16.9.P LEADZ INTEGER ARGUMENT OK'
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
end program i169p_leadz_integer_argument
