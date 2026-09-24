program i169i_exp_characteristics
  implicit none
  real :: real_xs(3) = [-1.0, 0.0, 1.0]
  complex :: complex_xs(2) = [(0.0, 0.5), (1.0, -0.5)]
  real :: real_scalar = 0.25
  complex :: complex_scalar = (0.25, 0.5)
  real(kind=kind(0.0d0)) :: double_scalar = 0.25d0
  complex(kind=kind(0.0d0)) :: double_complex = (0.25d0, 0.5d0)
  real :: real_observed
  complex :: complex_observed
  call require_true('exp elemental real array shape', all(shape(exp(real_xs)) == shape(real_xs)))
  call require_true('exp elemental complex array shape', all(shape(exp(complex_xs)) == shape(complex_xs)))
  real_observed = exp(real_scalar)
  complex_observed = exp(complex_scalar)
  call require_true('exp accepts real argument', kind(real_observed) == kind(real_scalar))
  call require_true('exp accepts complex argument', kind(complex_observed) == kind(complex_scalar))
  call require_true('exp real result kind follows x', kind(exp(double_scalar)) == kind(double_scalar))
  call require_true('exp complex result kind follows x', kind(exp(double_complex)) == kind(double_complex))
  write(*,'(a)') 'INTRINSICS 16.9.I EXP ARGUMENTS OK'
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
end program i169i_exp_characteristics
