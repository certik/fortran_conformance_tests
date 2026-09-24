module p3_external_m
  implicit none
  integer :: abs
  external :: abs
  character(len=5) :: ext_word
  external :: ext_word
contains
  integer function external_value()
    external_value = abs(-1)
  end function external_value
  integer function external_word_len()
    external_word_len = len(ext_word())
  end function external_word_len
  character(len=5) function external_word_value()
    external_word_value = ext_word()
  end function external_word_value
end module p3_external_m
program p3_external_probe
  use p3_external_m
  implicit none
  character(len=5) :: word
  if (external_value() /= 41) error stop
  if (external_word_len() /= 5) error stop
  word = external_word_value()
  if (len(word) /= 5) error stop
  if (word /= 'HELLO') error stop
  print '(a)', 'MODULE EXTERNAL PROCEDURE OK'
end program p3_external_probe
integer function abs(x)
  integer, intent(in) :: x
  abs = 42 + x
end function abs
character(len=5) function ext_word()
  ext_word = 'HELLO'
end function ext_word
