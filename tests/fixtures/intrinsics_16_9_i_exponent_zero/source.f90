program i169i_exponent_zero
  implicit none
  real :: zero = 0.0
  real :: negative_zero = -0.0
  call require_true('exponent positive zero result zero', exponent(zero) == 0)
  call require_true('exponent negative zero result zero', exponent(negative_zero) == 0)
  write(*,'(a)') 'INTRINSICS 16.9.I EXPONENT ZERO OK'
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
end program i169i_exponent_zero
