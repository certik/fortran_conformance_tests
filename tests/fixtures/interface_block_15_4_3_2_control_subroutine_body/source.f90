program interface_block_subroutine_body_control
  implicit none
  interface
    subroutine ext_sub_body()
    end subroutine ext_sub_body
  end interface
  print '(a)', 'INTERFACE BLOCK SUBROUTINE BODY CONTROL OK'
end program interface_block_subroutine_body_control
subroutine ext_sub_body()
  implicit none
end subroutine ext_sub_body
