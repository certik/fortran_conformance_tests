program i169i_exponent_model
  implicit none
  real :: default_x, default_power, negative_power
  real(kind=kind(0.0d0)) :: double_power
  integer, parameter :: default_power_k = 3
  integer, parameter :: double_power_k = 5
  default_x = real(radix(1.0), kind(1.0)) ** 2
  default_power = real(radix(default_x), kind(default_x)) ** default_power_k
  negative_power = -default_power
  double_power = real(radix(0.0d0), kind(0.0d0)) ** double_power_k
  call require_true('exponent exact radix power model exponent', &
       exponent(default_power) == default_power_k + 1)
  call require_true('exponent negative value uses same exponent', exponent(negative_power) == exponent(default_power))
  call require_true('exponent double kind model relation', exponent(double_power) == double_power_k + 1)
  write(*,'(a)') 'INTRINSICS 16.9.I EXPONENT MODEL OK'
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
end program i169i_exponent_model
