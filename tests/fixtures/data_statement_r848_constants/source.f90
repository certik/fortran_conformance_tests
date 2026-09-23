program data_statement_r848_constants
  implicit none
  integer, parameter :: named_constant = 73
  integer, target, save :: target_value
  integer :: scalar_integer, named_receiver, signed_negative, signed_positive
  real :: signed_real
  logical :: scalar_logical
  character(len=2) :: scalar_character
  complex :: scalar_complex
  integer, pointer :: null_pointer, target_pointer
  data scalar_integer, scalar_logical, scalar_character, scalar_complex, named_receiver &
       /71, .true., 'AB', (3.0,4.0), named_constant/
  data signed_negative, signed_positive, signed_real /-7, +11, -1.0/
  data target_value /79/
  data null_pointer /null()/
  data target_pointer /target_value/
  if (scalar_integer /= 71) error stop 1
  if (.not. scalar_logical) error stop 2
  if (len(scalar_character) /= 2) error stop 3
  if (scalar_character /= 'AB') error stop 4
  if (real(scalar_complex) /= 3.0) error stop 5
  if (aimag(scalar_complex) /= 4.0) error stop 6
  if (named_receiver /= 73) error stop 7
  if (signed_negative /= -7) error stop 8
  if (signed_positive /= 11) error stop 9
  if (signed_real /= -1.0) error stop 10
  if (associated(null_pointer)) error stop 11
  if (.not. associated(target_pointer, target_value)) error stop 12
  if (target_pointer /= 79) error stop 13
  write(*,'(a)') 'DATA STATEMENT R848 CONSTANTS OK'
end program data_statement_r848_constants
