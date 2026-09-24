program i169i_erfc_scaled_characteristics
  implicit none
  real :: xs(3) = [-0.5, 0.0, 0.5]
  real :: scalar_x = 0.25
  real(kind=kind(0.0d0)) :: double_x = 0.25d0
  real :: scalar_observed
  real(kind=kind(0.0d0)) :: double_observed
  call require_true('erfc_scaled elemental preserves shape', all(shape(erfc_scaled(xs)) == shape(xs)))
  scalar_observed = erfc_scaled(scalar_x)
  double_observed = erfc_scaled(double_x)
  call require_true('erfc_scaled accepts default real scalar', kind(scalar_observed) == kind(scalar_x))
  call require_true('erfc_scaled accepts double real scalar', kind(double_observed) == kind(double_x))
  call require_true('erfc_scaled result kind follows x expression', kind(erfc_scaled(double_x)) == kind(double_x))
  write(*,'(a)') 'INTRINSICS 16.9.I ERFC SCALED CHARACTERISTICS OK'
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
end program i169i_erfc_scaled_characteristics
