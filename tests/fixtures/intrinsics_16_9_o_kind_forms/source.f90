program i169o_kind_forms
  implicit none
  integer :: ints(-1:1) = [7, 8, 9]
  real :: real_value = 1.25
  complex :: complex_value = (2.0, -3.0)
  logical :: logical_value = .true.
  character(len=4) :: char_value = 'WXYZ'
  call require_true('kind admits all intrinsic type arguments', &
      kind(17) == kind(ints(0)) .and. kind(real_value) == kind(1.0) .and. &
      kind(complex_value) == kind((1.0, 0.0)) .and. kind(logical_value) == kind(.true.) .and. &
      kind(char_value) == kind('A'))
  call require_true('kind admits scalar and array arguments', &
      kind(ints) == kind(ints(0)) .and. kind(17) == kind(ints(0)))
  call require_true('kind result default integer scalar', &
      kind(kind(char_value)) == kind(0) .and. rank(kind(ints)) == 0)
  write(*,'(a)') 'INTRINSICS 16.9.O KIND FORMS OK'
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
end program i169o_kind_forms
