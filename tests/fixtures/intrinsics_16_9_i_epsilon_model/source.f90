program i169i_epsilon_model
  implicit none
  real :: default_x = 1.0
  real(kind=kind(0.0d0)) :: double_x = 1.0d0
  real :: default_expected
  real(kind=kind(0.0d0)) :: double_expected
  default_expected = real(radix(default_x), kind(default_x)) ** (1 - digits(default_x))
  double_expected = real(radix(double_x), kind(double_x)) ** (1 - digits(double_x))
  call require_true('epsilon default real model value', epsilon(default_x) == default_expected)
  call require_true('epsilon double real model value', epsilon(double_x) == double_expected)
  write(*,'(a)') 'INTRINSICS 16.9.I EPSILON MODEL OK'
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
end program i169i_epsilon_model
