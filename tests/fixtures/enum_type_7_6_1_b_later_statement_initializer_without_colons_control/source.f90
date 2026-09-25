program p
  implicit none
  enum, bind(c)
    enumerator first
    enumerator :: second=4
  end enum
end program p
