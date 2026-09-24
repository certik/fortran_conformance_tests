program i169i_epsilon_arguments
  implicit none
  real :: scalar_x = 1.25
  real :: array_x(3) = [1.0, 2.0, 4.0]
  call require_true('real scalar argument gives positive model epsilon', epsilon(scalar_x) > 0.0)
  call require_true('array argument still gives scalar result', rank(epsilon(array_x)) == 0)
  write(*,'(a)') 'INTRINSICS 16.9.I EPSILON ARGUMENTS OK'
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
end program i169i_epsilon_arguments
