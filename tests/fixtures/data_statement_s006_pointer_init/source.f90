program data_statement_s006_pointer_init
  implicit none
  integer, target, save :: target_value, other_target
  integer, pointer :: null_pointer, target_pointer
  data target_value, other_target /83, 89/
  data null_pointer /null()/
  data target_pointer /target_value/
  if (target_value /= 83) error stop 1
  if (other_target /= 89) error stop 2
  if (associated(null_pointer)) error stop 3
  if (.not. associated(target_pointer, target_value)) error stop 4
  if (target_pointer /= 83) error stop 5
  write(*,'(a)') 'DATA STATEMENT S006 POINTER INIT OK'
end program data_statement_s006_pointer_init
