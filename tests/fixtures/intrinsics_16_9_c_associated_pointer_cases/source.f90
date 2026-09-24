program i169c_associated_pointer_cases
  implicit none
  integer, target :: scalar_target = 61, other_scalar = 67
  integer, target :: array_target(4) = [1, 2, 3, 4]
  character(len=1), target :: nonzero_char = 'x'
  character(len=0), target :: zero_char = ''
  character(len=1), target :: nonzero_chars(1) = ['y']
  character(len=0), target :: zero_chars(1) = ['']
  integer, pointer :: p_scalar, q_scalar
  integer, pointer :: p_array(:), q_array(:)
  character(len=:), pointer :: p_char, q_char
  character(len=:), pointer :: p_chars(:), q_chars(:)
  p_scalar => scalar_target
  nullify(q_scalar)
  call require_false('scalar pointer target one disassociated false', associated(p_scalar, q_scalar))
  q_scalar => scalar_target
  call require_true('scalar pointer both associated true', associated(p_scalar, q_scalar))
  q_scalar => scalar_target
  call require_true('scalar pointer same target true', associated(p_scalar, q_scalar))
  q_scalar => other_scalar
  call require_false('scalar pointer distinct target false', associated(p_scalar, q_scalar))
  p_array => array_target
  nullify(q_array)
  call require_false('array pointer target one disassociated false', associated(p_array, q_array))
  q_array => array_target
  call require_true('array pointer both associated true', associated(p_array, q_array))
  q_array => array_target
  call require_true('array pointer same shape true', associated(p_array, q_array))
  q_array => array_target(1:3)
  call require_false('array pointer different shape false', associated(p_array, q_array))
  p_array => array_target(1:3)
  q_array => array_target(1:3)
  call require_true('array pointer same storage order true', associated(p_array, q_array))
  p_array => array_target(1:3)
  q_array => array_target(1:3)
  q_array => array_target(2:4)
  call require_false('array pointer shifted storage false', associated(p_array, q_array))
  p_char => nonzero_char
  q_char => nonzero_char
  call require_true('scalar pointer nonzero storage true', associated(p_char, q_char))
  p_char => zero_char
  q_char => zero_char
  call require_false('scalar pointer zero storage false', associated(p_char, q_char))
  p_array => array_target(1:0)
  q_array => array_target(1:0)
  call require_false('array pointer size zero false', associated(p_array, q_array))
  p_chars => nonzero_chars
  q_chars => nonzero_chars
  call require_true('array pointer element nonzero storage true', associated(p_chars, q_chars))
  p_chars => zero_chars
  q_chars => zero_chars
  call require_false('array pointer element zero storage false', associated(p_chars, q_chars))
  write(*,'(a)') 'INTRINSICS 16.9.C ASSOCIATED POINTER CASES OK'
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
end program i169c_associated_pointer_cases
