program interface_block_abstract_control
  implicit none
  abstract interface proc
    subroutine proc()
    end subroutine proc
  end interface
  print '(a)', 'INTERFACE BLOCK ABSTRACT CONTROL OK'
end program interface_block_abstract_control
