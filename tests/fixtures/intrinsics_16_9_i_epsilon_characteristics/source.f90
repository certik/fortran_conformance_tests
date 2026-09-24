program i169i_epsilon_characteristics
  implicit none
  real :: array_x(2) = [1.0, 2.0]
  real(kind=kind(0.0d0)) :: double_x = 1.0d0
  call require_true('epsilon array result is scalar', rank(epsilon(array_x)) == 0)
  call require_true('epsilon result has x kind', kind(epsilon(double_x)) == kind(double_x))
  write(*,'(a)') 'INTRINSICS 16.9.I EPSILON CHARACTERISTICS OK'
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
end program i169i_epsilon_characteristics
