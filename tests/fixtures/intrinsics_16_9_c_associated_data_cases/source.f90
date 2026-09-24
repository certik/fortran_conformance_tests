program i169c_associated_data_cases
  implicit none
  integer, target :: scalar_target = 53, other_scalar = 59
  integer, target :: array_target(4) = [1, 2, 3, 4]
  integer, target :: other_array(4) = [5, 6, 7, 8]
  character(len=1), target :: nonzero_char = 'x'
  character(len=0), target :: zero_char = ''
  character(len=1), target :: nonzero_chars(1) = ['y']
  character(len=0), target :: zero_chars(1) = ['']
  integer, pointer :: scalar_pointer
  integer, pointer :: array_pointer(:)
  character(len=:), pointer :: char_pointer
  character(len=:), pointer :: char_array_pointer(:)
  scalar_pointer => scalar_target
  call require_true('scalar same nonzero storage true', associated(scalar_pointer, scalar_target))
  call require_false('scalar wrong target false', associated(scalar_pointer, other_scalar))
  array_pointer => array_target
  call require_true('array same shape full true', associated(array_pointer, array_target))
  call require_false('array different target false', associated(array_pointer, other_array))
  call require_false('array different shape false', associated(array_pointer, array_target(1:3)))
  array_pointer => array_target(1:3)
  call require_true('array nonzero elements true', associated(array_pointer, array_target(1:3)))
  array_pointer => array_target(1:3)
  call require_false('array same shape shifted storage false', associated(array_pointer, array_target(2:4)))
  char_pointer => nonzero_char
  call require_true('scalar character nonzero storage true', associated(char_pointer, nonzero_char))
  char_pointer => zero_char
  call require_false('scalar character zero storage false', associated(char_pointer, zero_char))
  array_pointer => array_target(1:0)
  call require_false('array target size zero false', associated(array_pointer, array_target(1:0)))
  char_array_pointer => nonzero_chars
  call require_true('array element nonzero storage true', associated(char_array_pointer, nonzero_chars))
  char_array_pointer => zero_chars
  call require_false('array element zero storage false', associated(char_array_pointer, zero_chars))
  write(*,'(a)') 'INTRINSICS 16.9.C ASSOCIATED DATA CASES OK'
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
end program i169c_associated_data_cases
