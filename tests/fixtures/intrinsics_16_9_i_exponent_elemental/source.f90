program i169i_exponent_characteristics
  implicit none
  real :: xs(3) = [0.0, 1.0, -1.0]
  integer, parameter :: description_power = 2
  integer, parameter :: argument_power = 3
  real :: real_x
  real :: real_y
  real_x = real(radix(1.0), kind(1.0)) ** description_power
  real_y = real(radix(1.0), kind(1.0)) ** argument_power
  call require_true('exponent describes floating exponent value', &
       exponent(real_x) == description_power + 1)
  call require_true('exponent elemental shape', all(shape(exponent(xs)) == shape(xs)))
  call require_true('exponent accepts real x', exponent(real_y) == argument_power + 1)
  write(*,'(a)') 'INTRINSICS 16.9.I EXPONENT ELEMENTAL OK'
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
end program i169i_exponent_characteristics
